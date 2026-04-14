"""Report generator — Requirements 9.1, 9.2, 9.5."""
from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Report:
    """Full pipeline report document. Requirement 9.1."""
    job_id: str
    dataset_id: str
    user_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quality_score: Optional[float] = None
    completeness: Optional[float] = None
    consistency: Optional[float] = None
    accuracy: Optional[float] = None
    profile: Optional[dict] = None
    issues: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)
    outlier_summary: Optional[dict] = None
    anomaly_summary: Optional[dict] = None
    drift_summary: Optional[dict] = None
    semantic_types: Optional[dict] = None
    narrative: str = ""
    pdf_s3_key: Optional[str] = None


def serialize_report(report: Report) -> str:
    """Serialize Report to JSON string. Requirement 9.1."""
    return json.dumps(asdict(report), default=str)


def deserialize_report(data: str) -> Report:
    """Deserialize Report from JSON string. Requirement 9.1."""
    d = json.loads(data)
    return Report(**d)


def generate_pdf(report: Report) -> bytes:
    """Generate a PDF report using ReportLab. Requirement 9.2."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle("Title", parent=styles["Title"], alignment=TA_CENTER, fontSize=18)
        story.append(Paragraph("AI Data Quality Intelligence Report", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Metadata
        meta = [
            ["Job ID", report.job_id],
            ["Dataset ID", report.dataset_id],
            ["Generated", report.created_at],
        ]
        t = Table(meta, colWidths=[2 * inch, 4 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

        # Quality Scores
        story.append(Paragraph("Quality Scores", styles["Heading2"]))
        scores = [
            ["Metric", "Score"],
            ["Overall Quality", f"{report.quality_score:.1f}%" if report.quality_score is not None else "N/A"],
            ["Completeness", f"{report.completeness:.1f}%" if report.completeness is not None else "N/A"],
            ["Consistency", f"{report.consistency:.1f}%" if report.consistency is not None else "N/A"],
            ["Accuracy", f"{report.accuracy:.1f}%" if report.accuracy is not None else "N/A"],
        ]
        st = Table(scores, colWidths=[3 * inch, 3 * inch])
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14B8A6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0FDFA")]),
        ]))
        story.append(st)
        story.append(Spacer(1, 0.2 * inch))

        # Narrative
        if report.narrative:
            story.append(Paragraph("Executive Summary", styles["Heading2"]))
            story.append(Paragraph(report.narrative, styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

        # Issues
        if report.issues:
            story.append(Paragraph("Issues Found", styles["Heading2"]))
            for issue in report.issues:
                story.append(Paragraph(f"• {issue}", styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Fixes
        if report.fixes:
            story.append(Paragraph("Fixes Applied", styles["Heading2"]))
            for fix in report.fixes:
                story.append(Paragraph(f"✓ {fix}", styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Recommendations
        if report.recommendations:
            story.append(Paragraph("Recommendations", styles["Heading2"]))
            for rec in report.recommendations:
                col = rec.get("column", "")
                action = rec.get("action", "")
                reason = rec.get("reason", "")
                story.append(Paragraph(f"• [{col}] {action}: {reason}", styles["Normal"]))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        logger.warning("ReportLab not available; returning empty PDF bytes")
        return b"%PDF-1.4 placeholder"


async def save_report(
    report: Report,
    s3_bucket: str,
    mongo_collection,
    s3_client,
) -> str:
    """Generate PDF, upload to S3, save JSON to MongoDB. Returns S3 key. Requirement 9.5."""
    # Generate PDF
    pdf_bytes = generate_pdf(report)
    s3_key = f"reports/{report.job_id}/report.pdf"

    # Upload to S3
    try:
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        report.pdf_s3_key = s3_key
    except Exception as exc:
        logger.error("Failed to upload PDF to S3: %s", exc)

    # Save to MongoDB
    try:
        doc = json.loads(serialize_report(report))
        doc["_id"] = report.job_id
        await mongo_collection.replace_one({"_id": report.job_id}, doc, upsert=True)
    except Exception as exc:
        logger.error("Failed to save report to MongoDB: %s", exc)

    return s3_key
