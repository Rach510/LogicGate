from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether

from lib.db import db
from routers.analytics import get_analytics
from routers.budgets import get_budget

router = APIRouter(prefix="/projects", tags=["reports"])


def _money(value: str) -> str:
    return value or "Not available"


@router.get("/{project_id}/report/pdf")
async def export_project_report(project_id: str, scope: str = Query("full", pattern="^(full|frame)$")):
    project = await db.projects.find_one({"id": project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    stored = await db.video_analysis.find_one({"project_id": project_id})
    if stored:
        result = stored.get("result", {})
    else:
        result = {}

    measurements = result.get("activeMeasurements", {})
    boxes = result.get("boxes", [])
    confidence = float(measurements.get("confidence", 0))
    quality = float(measurements.get("quality", 0))
    road_width = float(measurements.get("roadWidth", 0))
    left_lane = float(measurements.get("leftLane", 0))
    kerb = float(measurements.get("kerbToKerb", 0))

    analytics = await get_analytics(project_id)
    budget = await get_budget(project_id)
    budget_total = budget.total

    latest_brief = await db.ai_road_briefs.find_one({"project_id": project_id}, sort=[("created_at", -1)])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"RoadRead Report - {project.get('name', project_id)}",
        author="RoadRead",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RoadTitle", parent=styles["Title"], fontSize=22, leading=26, textColor=colors.HexColor("#18332a"), spaceAfter=5))
    styles.add(ParagraphStyle(name="Sub", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#60716a"), spaceAfter=12))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#18332a"), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#33443e")))

    story = [
        Paragraph("ROADREAD", styles["RoadTitle"]),
        Paragraph(
            f"{scope.title()} survey report · Generated {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}",
            styles["Sub"],
        ),
        Paragraph("Project & survey context", styles["Section"]),
    ]

    context = [
        ["Project", project.get("name", "—")],
        ["Route", project.get("route", "—")],
        ["Location", (project.get("location") or {}).get("address", "—")],
        ["Condition", project.get("condition", "—")],
        ["Coverage", project.get("coverage", "—")],
        ["Media", result.get("resolution", "—")],
    ]
    story.append(_table(context))

    story.append(Paragraph("Measurements & trust metrics", styles["Section"]))
    measurements_table = [
        ["Metric", "Value"],
        ["Road width", f"{road_width:.2f} m"],
        ["Left lane", f"{left_lane:.2f} m"],
        ["Kerb-to-kerb", f"{kerb:.2f} m"],
        ["Model confidence", f"{confidence:.1f}%"],
        ["Capture quality", f"{quality:.1f}%"],
        ["Analyzed frames", str(result.get("analyzedFrames", 0))],
    ]
    story.append(_table(measurements_table, header=True))

    story.append(Paragraph("Detected defects", styles["Section"]))
    if boxes:
        defect_rows = [["Detection", "Severity", "Confidence"]]
        for box in boxes:
            defect_rows.append([
                box.get("label", "Detection"),
                str(box.get("severity", "—")).title(),
                f"{float(box.get('confidence', 0)):.1f}%",
            ])
        story.append(_table(defect_rows, header=True))
    else:
        story.append(Paragraph("No defects were detected in the analyzed media.", styles["BodySmall"]))

    if scope == "full":
        story.append(Paragraph("Analytics & budget", styles["Section"]))
        story.append(_table([
            ["Road condition", analytics.roadCondition],
            ["Defects detected", str(analytics.defectsDetected)],
            ["Analyzed distance", analytics.analyzedDistance],
            ["Overall budget estimate", _money(budget_total)],
        ]))

        if budget.materials:
            story.append(Paragraph("Cost breakdown", styles["Section"]))
            cost_rows = [["Item", "Estimate"]] + [[m.name, m.amount] for m in budget.materials]
            story.append(_table(cost_rows, header=True))

        if analytics.reports:
            story.append(Paragraph("Field notes & follow-ups", styles["Section"]))
            for report in analytics.reports:
                story.append(Paragraph(f"<b>{report.title}</b> · {report.category} · {report.created}", styles["BodySmall"]))
                story.append(Paragraph(report.note, styles["BodySmall"]))
                story.append(Spacer(1, 4))

        if latest_brief:
            story.append(Paragraph("Latest AI road brief", styles["Section"]))
            story.append(Paragraph(str(latest_brief.get("content", "" )).replace("\n", "<br/>"), styles["BodySmall"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "RoadRead note: computer-vision measurements are estimates unless a calibrated reference is supplied. "
        "Verify dimensions, quantities and safety-critical decisions in the field before procurement or construction.",
        styles["BodySmall"],
    ))

    doc.build(story)
    buffer.seek(0)
    filename = f"roadread-{project_id}-{scope}-report.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _table(rows: list[list[str]], header: bool = False) -> Table:
    column_count = len(rows[0]) if rows else 2
    widths = [58 * mm, 112 * mm] if column_count == 2 else [75 * mm, 47 * mm, 48 * mm]
    table = Table(rows, colWidths=widths[:column_count])
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#33443e")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8e0dc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18332a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    table.setStyle(TableStyle(style))
    return table
