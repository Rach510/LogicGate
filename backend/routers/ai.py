import json
import logging
import os
import uuid
from datetime import timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from lib.db import db
from models.ai import AiRoadBrief, AiRoadBriefRequest

# `emergentintegrations` is a proprietary package only present on the Emergent.sh pod.
# Import it lazily so `import server` and every other route keep working in any other
# environment (local dev, CI, this sandbox) — only /ai/road-brief/stream needs it.
try:
    from emergentintegrations.llm.chat import LlmChat, StreamDone, TextDelta, UserMessage
    _AI_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover - depends on the deployment environment
    LlmChat = StreamDone = TextDelta = UserMessage = None  # type: ignore[assignment]
    _AI_IMPORT_ERROR = exc


router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


SYSTEM_MESSAGE = """You are RoadRead's senior road-infrastructure analyst for Indian municipal and highway projects.
Write a concise, decision-ready road brief from only the supplied measurements. Use plain professional English.
Return exactly three short sections with these headings: Assessment, Priority actions, Budget note.
Mention meaningful measurements and confidence, avoid invented facts, and state that field verification is required
before procurement or safety-critical work. Keep the complete brief under 220 words."""


@router.post("/road-brief/stream")
async def stream_road_brief(payload: AiRoadBriefRequest):
    if _AI_IMPORT_ERROR is not None:
        raise HTTPException(status_code=503, detail="AI integration is unavailable in this environment")
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI integration is not configured")

    prompt = f"""Create a RoadRead project brief for:
Project: {payload.project_name}
Route: {payload.route}
Road condition: {payload.condition}
Model confidence: {payload.confidence}%
Capture quality: {payload.quality}%
Detected defects: {payload.defects_detected}
Road width: {payload.road_width} m
Left lane width: {payload.left_lane} m
Kerb-to-kerb: {payload.kerb_to_kerb} m
Current repair estimate: {payload.budget_total}

Use the measurements directly and prioritize practical next steps for an Indian infrastructure team."""

    async def event_generator():
        content_parts: list[str] = []
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=f"roadread-{payload.project_id}-{uuid.uuid4()}",
                system_message=SYSTEM_MESSAGE,
            ).with_model("openai", "gpt-5.4")

            async for event in chat.stream_message(UserMessage(text=prompt)):
                if isinstance(event, TextDelta):
                    content_parts.append(event.content)
                    data = json.dumps({"type": "delta", "content": event.content})
                    yield f"data: {data}\n\n"
                elif isinstance(event, StreamDone):
                    break

            content = "".join(content_parts).strip()
            if not content:
                raise RuntimeError("The AI model returned an empty road brief")
            brief = AiRoadBrief(project_id=payload.project_id, content=content)
            await db.ai_road_briefs.insert_one(brief.model_dump())
            data = json.dumps({"type": "done", "brief": brief.model_dump(mode="json")})
            yield f"data: {data}\n\n"
        except Exception as exc:
            logger.exception("RoadRead AI brief generation failed")
            data = json.dumps({"type": "error", "message": "RoadRead AI could not generate this brief. Please try again."})
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/road-briefs/{project_id}", response_model=list[AiRoadBrief])
async def list_road_briefs(project_id: str):
    documents = await db.ai_road_briefs.find({"project_id": project_id}).sort("created_at", -1).to_list(10)
    briefs: list[AiRoadBrief] = []
    for document in documents:
        created_at = document.get("created_at")
        if created_at is not None and created_at.tzinfo is None:
            document["created_at"] = created_at.replace(tzinfo=timezone.utc)
        briefs.append(AiRoadBrief(**document))
    return briefs
