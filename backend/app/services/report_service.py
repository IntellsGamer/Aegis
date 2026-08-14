"""PDF report export built on ReportLab (pure-Python, open-source)."""
from __future__ import annotations

import io
from datetime import datetime

from app.models import Scan
from app.trust_engine.engine import risk_level_for


def _render_with_reportlab(scan: Scan, reasons: list, recommendations: list) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm)

    h1 = ParagraphStyle("h1", fontSize=20, leading=24, textColor=colors.HexColor("#0ea5e9"))
    h2 = ParagraphStyle("h2", fontSize=13, leading=18, spaceBefore=10,
                        textColor=colors.HexColor("#334155"))
    body = ParagraphStyle("body", fontSize=9.5, leading=13, spaceAfter=4)

    story = []
    story.append(Paragraph("AEGIS Digital Trust Report", h1))
    story.append(Paragraph(f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0ea5e9")))
    story.append(Paragraph(f"Scan ID: #{scan.id} &nbsp;&nbsp; Type: {scan.scan_type}", body))

    score_color = colors.HexColor("#22c55e")
    if scan.risk_level in ("medium", "high", "critical"):
        score_color = {"medium": "#eab308", "high": "#f97316", "critical": "#ef4444"}[scan.risk_level]

    story.append(Spacer(1, 6))
    score_table = Table(
        [
            ["Trust Score", "Risk Level", "Confidence"],
            [f"{scan.trust_score}/100", scan.risk_level.upper(), f"{scan.confidence:.0%}"],
        ],
        colWidths=[60 * mm, 60 * mm, 60 * mm],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (1, 1), (1, 1), score_color),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, 1), 14),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(score_table)

    story.append(Paragraph("Summary", h2))
    story.append(Paragraph(scan.summary or "Analysis complete.", body))

    story.append(Paragraph("Why this score", h2))
    if reasons:
        rows = [["Indicator", "Impact", "Severity"]]
        for reason in reasons:
            rows.append([
                reason.get("title") or reason.get("code") or "Signal",
                f"{float(reason.get('impact') or 0):+.0f}",
                reason.get("severity") or "info",
            ])
        table = Table(rows, colWidths=[120 * mm, 40 * mm, 40 * mm])
        table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.4, colors.grey),
            ("GRID", (0, 1), (-1, -1), 0.2, colors.lightgrey),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No significant indicators were detected.", body))

    story.append(Paragraph("Recommendations", h2))
    for rec in recommendations:
        story.append(Paragraph(f"&bull; {rec}", body))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "AEGIS is an advisory tool. Always verify sensitive messages through "
        "an independent official channel.", body
    ))
    doc.build(story)
    return buf.getvalue()


def generate_pdf(scan: Scan, reasons: list, recommendations: list) -> bytes | None:
    """Generate a PDF report; returns None if ReportLab is unavailable."""
    try:
        return _render_with_reportlab(scan, reasons, recommendations)
    except ImportError:
        return None
    except Exception as exc:  # pragma: no cover
        import logging

        logging.getLogger("aegis.report").exception("pdf generation failed: %s", exc)
        return None
