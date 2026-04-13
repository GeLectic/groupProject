import re
from datetime import datetime, timezone
from typing import Any, Dict, List


def _norm_location(location: str) -> str:
    location = (location or "").lower().strip()
    location = re.sub(r"[^a-z0-9\s]", "", location)
    location = re.sub(r"\s+", " ", location)
    return location


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_block(block: Dict[str, Any], destination: str, part: str) -> Dict[str, Any]:
    normalized = dict(block)

    has_activity = _has_text(normalized.get("activity"))
    has_location = _has_text(normalized.get("location"))

    if not has_location:
        normalized["location"] = destination
    if not has_activity and has_location:
        location = str(normalized.get("location")).strip()
        normalized["activity"] = f"Explore {location}" if location else "Flexible local exploration"
    if not has_activity and not has_location:
        normalized["activity"] = "Flexible local exploration"
        normalized["location"] = "Near city center"

    if not _has_text(normalized.get("tip")):
        normalized["tip"] = f"Check local timings and commute conditions before the {part}."

    return normalized


def deduplicate_locations(itinerary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    day_parts = ["morning", "afternoon", "evening", "night"]

    for day in itinerary:
        for part in day_parts:
            block = day.get(part)
            if not isinstance(block, dict):
                continue
            normalized_block = _normalize_block(block, destination=day.get("destination", ""), part=part)
            day[part] = normalized_block

            location = normalized_block.get("location")
            norm = _norm_location(str(location))
            if not norm:
                continue

            if norm in seen:
                # Keep real repeated locations when meaningful; only annotate potential overlap.
                note = "Location appears more than once; keep if intended for different time windows."
                existing_notes = str(day.get("day_notes", "")).strip()
                if note not in existing_notes:
                    day["day_notes"] = (existing_notes + " " + note).strip()
            else:
                seen.add(norm)

    return itinerary


def assemble_final_itinerary(
    destination: str,
    days: int,
    month: str,
    budget_level: str,
    travel_style: str,
    itinerary_data: List[Dict[str, Any]],
    hotels: Dict[str, Any],
    tips: Dict[str, Any],
    data_sources: Dict[str, Any],
    notices: List[str],
) -> Dict[str, Any]:
    itinerary_with_destination = []
    for day in itinerary_data:
        if isinstance(day, dict):
            cloned = dict(day)
            cloned.setdefault("destination", destination)
            itinerary_with_destination.append(cloned)

    itinerary = deduplicate_locations(itinerary_with_destination)
    for day in itinerary:
        day.pop("destination", None)

    return {
        "destination": destination,
        "days": days,
        "month": month,
        "budget_level": budget_level,
        "travel_style": travel_style,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "itinerary": itinerary,
        "hotels": {
            "budget": hotels.get("budget", []),
            "mid_range": hotels.get("mid_range", []),
            "luxury": hotels.get("luxury", []),
        },
        "hidden_gems": tips.get("hidden_gems", []),
        "warnings": tips.get("warnings", []),
        "must_eat": tips.get("must_eat", []),
        "cultural_tips": tips.get("cultural_tips", []),
        "packing": tips.get("packing_essentials", []),
        "budget_breakdown": tips.get("budget_breakdown", {}),
        "data_sources": data_sources,
        "notices": notices,
    }
