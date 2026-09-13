import logging

from fastapi import APIRouter

from lib.db import db
from models.issue import IssueReportDocument, IssueReportRequest, IssueReportResponse

router = APIRouter(prefix="/issues", tags=["issues"])
logger = logging.getLogger(__name__)


@router.post("", response_model=IssueReportResponse)
async def submit_issue(payload: IssueReportRequest):
    status = "received" if payload.attachmentName else "submitted"
    document = IssueReportDocument(
        description=payload.description,
        category=payload.category,
        location=payload.location,
        attachmentName=payload.attachmentName,
        project_id=payload.project_id,
        status=status,
    )
    await db.issues.insert_one(document.model_dump())
    return IssueReportResponse(id=document.id, status=document.status)
