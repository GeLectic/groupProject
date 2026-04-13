from html import escape
from io import BytesIO
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _as_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip() or fallback
    return str(value)


def _line(label: str, value: Any) -> str:
    text = _as_text(value)
    return f"<b>{escape(label)}:</b> {escape(text)}" if text else ""


def _list_section(story: List[Any], title: str, rows: List[Dict[str, Any]], style_heading: ParagraphStyle, style_body: ParagraphStyle) -> None:
    if not rows:
        return

    story.append(Paragraph(escape(title), style_heading))
    story.append(Spacer(1, 0.18 * cm))

    for row in rows:
        if not isinstance(row, dict):
            continue
        name = _as_text(row.get("name") or row.get("dish") or row.get("issue"), "Item")
        story.append(Paragraph(f"<b>{escape(name)}</b>", style_body))
        for key, value in row.items():
            if key in {"name", "dish", "issue"}:
                continue
            line = _line(key.replace("_", " ").title(), value)
            if line:
                story.append(Paragraph(line, style_body))
        story.append(Spacer(1, 0.12 * cm))

    story.append(Spacer(1, 0.26 * cm))


def build_itinerary_pdf(payload: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
        title="WanderMind Itinerary",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=colors.HexColor("#5e4315"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor("#6d4d16"),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=13,
        textColor=colors.HexColor("#1f1a12"),
    )

    story: List[Any] = []

    destination = _as_text(payload.get("destination"), "Unknown Destination")
    days = _as_text(payload.get("days"), "-")
    month = _as_text(payload.get("month"), "-")
    budget_level = _as_text(payload.get("budget_level"), "-")
    travel_style = _as_text(payload.get("travel_style"), "-")

    story.append(Paragraph(f"WanderMind Travel Dossier: {escape(destination)}", title_style))
    story.append(
        Paragraph(
            f"{escape(days)} days | {escape(month)} | {escape(budget_level)} | {escape(travel_style)}",
            body_style,
        )
    )
    story.append(Spacer(1, 0.34 * cm))

    itinerary = payload.get("itinerary", [])
    if isinstance(itinerary, list) and itinerary:
        story.append(Paragraph("Day-by-Day Itinerary", section_style))
        for day in itinerary:
            if not isinstance(day, dict):
                continue
            day_num = _as_text(day.get("day"), "-")
            theme = _as_text(day.get("theme"), "Daily Plan")
            story.append(Paragraph(f"<b>Day {escape(day_num)}</b> - {escape(theme)}", body_style))

            for part in ["morning", "afternoon", "evening", "night"]:
                block = day.get(part)
                if not isinstance(block, dict):
                    continue
                activity = _as_text(block.get("activity"), "")
                location = _as_text(block.get("location"), "")
                tip = _as_text(block.get("tip"), "")
                if activity or location:
                    story.append(
                        Paragraph(
                            f"<b>{escape(part.title())}</b>: {escape(activity)}"
                            f"{' | ' + escape(location) if location else ''}",
                            body_style,
                        )
                    )
                if tip:
                    story.append(Paragraph(f"Tip: {escape(tip)}", body_style))

            travel_times = day.get("travel_times", [])
            if isinstance(travel_times, list) and travel_times:
                tt_text = []
                for item in travel_times:
                    if not isinstance(item, dict):
                        continue
                    from_loc = _as_text(item.get("from"), "-")
                    to_loc = _as_text(item.get("to"), "-")
                    mins = _as_text(item.get("minutes"), "-")
                    mode = _as_text(item.get("mode"), "-")
                    tt_text.append(f"{from_loc} -> {to_loc} ({mins} min, {mode})")
                if tt_text:
                    story.append(Paragraph(f"Travel times: {escape('; '.join(tt_text))}", body_style))

            warnings = day.get("opening_hours_warnings", [])
            if isinstance(warnings, list) and warnings:
                story.append(Paragraph(f"Opening warnings: {escape('; '.join(str(w) for w in warnings))}", body_style))

            notes = _as_text(day.get("day_notes"), "")
            if notes:
                story.append(Paragraph(f"Notes: {escape(notes)}", body_style))

            story.append(Spacer(1, 0.22 * cm))

    hotels = payload.get("hotels", {})
    if isinstance(hotels, dict):
        story.append(Paragraph("Hotel Picks", section_style))
        for tier_key, tier_label in [("budget", "Budget"), ("mid_range", "Mid-Range"), ("luxury", "Luxury")]:
            rows = hotels.get(tier_key, [])
            if not isinstance(rows, list) or not rows:
                continue
            story.append(Paragraph(escape(tier_label), body_style))
            for row in rows:
                if not isinstance(row, dict):
                    continue
                name = _as_text(row.get("name"), "Suggested Stay")
                area = _as_text(row.get("area"), "")
                price = _as_text(row.get("est_cost_per_night_inr") or row.get("est_cost_per_night_usd"), "Estimated")
                story.append(Paragraph(f"- <b>{escape(name)}</b> | {escape(area)} | {escape(price)}", body_style))
            story.append(Spacer(1, 0.14 * cm))
        story.append(Spacer(1, 0.2 * cm))

    _list_section(story, "Hidden Gems", payload.get("hidden_gems", []), section_style, body_style)
    _list_section(story, "Warnings", payload.get("warnings", []), section_style, body_style)
    _list_section(story, "Must Eat", payload.get("must_eat", []), section_style, body_style)

    cultural_tips = payload.get("cultural_tips", [])
    if isinstance(cultural_tips, list) and cultural_tips:
        story.append(Paragraph("Cultural Tips", section_style))
        for tip in cultural_tips:
            story.append(Paragraph(f"- {escape(_as_text(tip))}", body_style))
        story.append(Spacer(1, 0.24 * cm))

    packing = payload.get("packing", [])
    if isinstance(packing, list) and packing:
        story.append(Paragraph("Packing Essentials", section_style))
        story.append(Paragraph(escape(", ".join(_as_text(x) for x in packing)), body_style))
        story.append(Spacer(1, 0.22 * cm))

    budget = payload.get("budget_breakdown", {})
    if isinstance(budget, dict) and budget:
        story.append(Paragraph("Budget Breakdown", section_style))
        table_rows = [["Category", "Estimate"]]
        for key, value in budget.items():
            table_rows.append([key.replace("_", " ").title(), _as_text(value)])

        table = Table(table_rows, colWidths=[7.2 * cm, 7.2 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d7b16a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f1608")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b48d45")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fffaf1")),
                ]
            )
        )
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
