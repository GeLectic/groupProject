import asyncio
import json
import re
from typing import Any, Dict, List

from config import settings
from utils.groq_client import GroqClient


USD_TO_INR_RATE = 83.0


def _extract_json_block(text: str) -> Any:
    text = text.strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for pattern in (r"\[[\s\S]*\]", r"\{[\s\S]*\}"):
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
    return None


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _extract_numeric_amount(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.replace(",", " ").strip()
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    if not matches:
        return None
    nums = [float(m) for m in matches]

    if "-" in text and len(nums) >= 2:
        return (nums[0] + nums[1]) / 2.0
    return nums[0]


def _format_inr(amount: float) -> str:
    rounded = int(round(amount))
    return f"INR {rounded:,}"


def _normalize_price_to_inr(row: Dict[str, Any]) -> str:
    inr_value = row.get("est_cost_per_night_inr") or row.get("est_cost_per_night")
    usd_value = row.get("est_cost_per_night_usd")

    if isinstance(inr_value, str) and any(token in inr_value.lower() for token in ["inr", "rs", "₹"]):
        return inr_value.strip()

    inr_numeric = _extract_numeric_amount(inr_value)
    if inr_numeric is not None:
        return _format_inr(inr_numeric)

    usd_numeric = _extract_numeric_amount(usd_value)
    if usd_numeric is not None:
        return _format_inr(usd_numeric * USD_TO_INR_RATE)

    if isinstance(usd_value, str) and usd_value.strip():
        return f"INR estimate (from {usd_value.strip()})"

    return "INR Estimated"


def _normalize_day(day: Any, day_num: int, destination: str) -> Dict[str, Any]:
    item = _safe_dict(day)

    def _timeline(block: Any, default_activity: str) -> Dict[str, Any]:
        source = _safe_dict(block)
        return {
            "time": source.get("time") or "",
            "activity": source.get("activity") or default_activity,
            "location": source.get("location") or destination,
            "tip": source.get("tip") or "Verify timings locally before departure.",
            "travel_time_from_hotel": source.get("travel_time_from_hotel") or "",
            "food_nearby": source.get("food_nearby") or "",
            "dinner_spot": source.get("dinner_spot") or "",
        }

    morning = _timeline(item.get("morning"), "Morning local exploration")
    afternoon = _timeline(item.get("afternoon"), "Afternoon sightseeing circuit")
    evening = _timeline(item.get("evening"), "Evening cultural walk")

    night_source = _safe_dict(item.get("night"))
    night = {
        "optional": bool(night_source.get("optional", True)),
        "activity": night_source.get("activity") or "Leisure time",
        "location": night_source.get("location") or destination,
    }

    try:
        day_value = int(item.get("day", day_num))
    except Exception:
        day_value = day_num

    return {
        "day": day_value,
        "theme": item.get("theme") or f"Day {day_num} Highlights",
        "morning": morning,
        "afternoon": afternoon,
        "evening": evening,
        "night": night,
        "day_notes": item.get("day_notes") or "Keep this day flexible for weather and local advice.",
        "travel_times": _safe_list(item.get("travel_times")),
        "opening_hours_warnings": [str(x) for x in _safe_list(item.get("opening_hours_warnings"))],
    }


def _normalize_itinerary_days(raw_days: Any, total_days: int, destination: str) -> List[Dict[str, Any]]:
    source_days = _safe_list(raw_days)
    normalized = [_normalize_day(day, idx + 1, destination) for idx, day in enumerate(source_days[:total_days])]

    while len(normalized) < total_days:
        normalized.append(_normalize_day({}, len(normalized) + 1, destination))

    return normalized


def _normalize_hotels(raw_hotels: Any, destination: str) -> Dict[str, List[Dict[str, Any]]]:
    hotels = _safe_dict(raw_hotels)

    def _normalize_tier(tier_key: str) -> List[Dict[str, Any]]:
        rows = [row for row in _safe_list(hotels.get(tier_key)) if isinstance(row, dict)]
        output: List[Dict[str, Any]] = []
        for i, row in enumerate(rows[:3], start=1):
            output.append(
                {
                    "name": row.get("name") or f"Recommended {tier_key.replace('_', ' ')} stay {i}",
                    "area": row.get("area") or destination,
                    "est_cost_per_night_inr": _normalize_price_to_inr(row),
                    "pros": row.get("pros") or "Convenient for travelers.",
                    "cons": row.get("cons") or "Availability may vary.",
                    "best_for": row.get("best_for") or tier_key.replace("_", " "),
                }
            )

        while len(output) < 3:
            idx = len(output) + 1
            output.append(
                {
                    "name": f"Recommended {tier_key.replace('_', ' ')} stay {idx}",
                    "area": destination,
                    "est_cost_per_night_inr": "INR Estimated",
                    "pros": "Convenient for travelers.",
                    "cons": "Availability may vary.",
                    "best_for": tier_key.replace("_", " "),
                }
            )
        return output

    return {
        "budget": _normalize_tier("budget"),
        "mid_range": _normalize_tier("mid_range"),
        "luxury": _normalize_tier("luxury"),
    }


def _normalize_tips(raw_tips: Any, destination: str, month: str, days: int) -> Dict[str, Any]:
    tips = _safe_dict(raw_tips)

    hidden = [row for row in _safe_list(tips.get("hidden_gems")) if isinstance(row, dict)]
    warnings = [row for row in _safe_list(tips.get("warnings")) if isinstance(row, dict)]
    must_eat = [row for row in _safe_list(tips.get("must_eat")) if isinstance(row, dict)]
    cultural = [str(x) for x in _safe_list(tips.get("cultural_tips"))]
    packing = [str(x) for x in _safe_list(tips.get("packing_essentials"))]

    while len(hidden) < 5:
        idx = len(hidden) + 1
        hidden.append(
            {
                "name": f"Local hidden spot {idx}",
                "why_special": "Recommended by traveler discussions.",
                "how_to_get_there": f"Use local transport guidance in {destination}.",
            }
        )
    while len(warnings) < 5:
        warnings.append({"issue": "Weather and road updates", "advice": "Check local advisories before day trips."})
    while len(must_eat) < 5:
        must_eat.append(
            {
                "dish": "Regional specialty",
                "where_to_find": "Local market area",
                "approx_cost": "Varies by restaurant",
            }
        )
    while len(cultural) < 4:
        cultural.append("Respect local customs and dress guidance at religious sites.")
    while len(packing) < 5:
        packing.append(f"Season-appropriate layers for {month}")

    budget = _safe_dict(tips.get("budget_breakdown"))
    budget.setdefault("accommodation_per_night", "Estimated")
    budget.setdefault("food_per_day", "Estimated")
    budget.setdefault("transport_total", "Estimated")
    budget.setdefault("activities_total", "Estimated")
    budget.setdefault(f"total_estimated_{days}_days", "Estimated")

    return {
        "hidden_gems": hidden[:5],
        "warnings": warnings[:5],
        "must_eat": must_eat[:5],
        "cultural_tips": cultural[:4],
        "packing_essentials": packing[:8],
        "budget_breakdown": budget,
    }


class ItineraryGenerator:
    def __init__(self, groq_client: GroqClient) -> None:
        self.groq_client = groq_client

    async def _chat_json(self, system_prompt: str, user_prompt: str) -> Any:
        if not self.groq_client.enabled:
            return None
        try:
            raw = await self.groq_client.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=settings.max_groq_output_tokens,
                temperature=0.2,
            )
            return _extract_json_block(raw)
        except Exception:
            return None

    def _fallback_days(self, days: int, destination: str) -> List[Dict[str, Any]]:
        result = []
        for day in range(1, days + 1):
            result.append(
                {
                    "day": day,
                    "theme": "Exploration & Local Culture",
                    "morning": {
                        "time": "8am-12pm",
                        "activity": "Visit a popular neighborhood and local landmark",
                        "location": destination,
                        "tip": "Start early to avoid crowds.",
                        "travel_time_from_hotel": "20-30 min",
                    },
                    "afternoon": {
                        "time": "12pm-5pm",
                        "activity": "Local market walk and museum or viewpoint",
                        "location": destination,
                        "food_nearby": "Try a highly rated local restaurant",
                        "tip": "Keep cash for small shops.",
                    },
                    "evening": {
                        "time": "5pm-9pm",
                        "activity": "Sunset stop and cultural walk",
                        "location": destination,
                        "dinner_spot": "Choose a well-reviewed regional cuisine place",
                        "tip": "Pre-book dinner on weekends.",
                    },
                    "night": {"optional": True, "activity": "Cafe or live music", "location": destination},
                    "day_notes": "Flexible plan due to limited verified traveler data.",
                }
            )
        return result

    async def generate(
        self,
        destination: str,
        days: int,
        month: str,
        budget_level: str,
        travel_style: str,
        places_context: str,
        hotel_context: str,
        community_context: str,
        conflicts_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.groq_client.enabled:
            fallback_days = _normalize_itinerary_days(self._fallback_days(days, destination), days, destination)
            hotels = _normalize_hotels({}, destination)
            tips = _normalize_tips({}, destination, month, days)
            return {
                "itinerary": fallback_days,
                "hotels": hotels,
                "tips": tips,
            }

        call_1 = await self._chat_json(
            system_prompt=(
                f"You are an expert local travel guide for {destination}. "
                "Use ONLY facts from the provided traveler-sourced context. "
                "Never fabricate locations. If data is sparse, say so honestly."
            ),
            user_prompt=(
                f"Context from real travelers: {places_context}\n"
                f"Create a detailed {days}-day itinerary for {destination} in {month} "
                f"for a {budget_level} {travel_style} traveler. "
                "For EACH day return a JSON object with this exact structure: "
                "{"
                "day: int,"
                "theme: string,"
                "morning: { time: '8am-12pm', activity, location, tip, travel_time_from_hotel },"
                "afternoon: { time: '12pm-5pm', activity, location, food_nearby, tip },"
                "evening: { time: '5pm-9pm', activity, location, dinner_spot, tip },"
                "night: { optional: true, activity, location },"
                "day_notes: string"
                "}."
                f" Return a JSON array of {days} day objects using valid JSON with double quotes only. "
                "Every day must contain all keys. Return nothing except JSON."
            ),
        )

        itinerary_days = _normalize_itinerary_days(call_1, days, destination)

        await asyncio.sleep(2)

        call_2 = await self._chat_json(
            system_prompt="You are a travel logistics expert.",
            user_prompt=(
                f"Given this itinerary: {json.dumps(itinerary_days)} "
                "Optimize each day for: "
                "- Geographic clustering: group nearby locations on same day "
                f"- Opening hours in {month}: note any closed days or seasonal closures "
                "- Realistic travel times between each stop (estimate in minutes) "
                "Return the same JSON structure with added fields: "
                "travel_times: [{from, to, minutes, mode}] "
                "opening_hours_warnings: [string] "
                "Do not change the activities, only add logistics. "
                "Always include travel_times and opening_hours_warnings for every day (empty list allowed). "
                "Return valid JSON only."
            ),
        )

        if isinstance(call_2, list):
            itinerary_days = _normalize_itinerary_days(call_2, days, destination)

        await asyncio.sleep(2)

        call_3 = await self._chat_json(
            system_prompt=f"You are a hospitality expert for {destination}.",
            user_prompt=(
                f"Traveler-reported accommodation context: {hotel_context} "
                "Recommend exactly 3 hotels or stays per budget tier. "
                "Return JSON: {"
                "budget: [ {name, area, est_cost_per_night_inr, pros, cons, best_for} ],"
                "mid_range: [ ... ],"
                "luxury: [ ... ]"
                "}. "
                "All prices must be in INR and marked as estimated. Use traveler context first, your knowledge second. "
                "Flag if any hotel had mixed reviews. "
                "Return exactly 3 objects per tier and valid JSON only."
            ),
        )

        hotels = _normalize_hotels(call_3, destination)

        await asyncio.sleep(2)

        call_4 = await self._chat_json(
            system_prompt="You are a travel safety and insider tips expert.",
            user_prompt=(
                f"Community-sourced context: {community_context} "
                f"Conflicts detected: {json.dumps(conflicts_list)} "
                "Extract and return JSON: {"
                "hidden_gems: [ {name, why_special, how_to_get_there} ],"
                "warnings: [ {issue, advice} ],"
                "must_eat: [ {dish, where_to_find, approx_cost} ],"
                "cultural_tips: [ string ],"
                f"packing_essentials: [ string ], budget_breakdown: {{ accommodation_per_night, food_per_day, transport_total, activities_total, total_estimated_{days}_days }}"
                "}. Return exactly 5 hidden_gems, 5 warnings, 5 must_eat, and 4 cultural_tips. "
                "Return valid JSON only."
            ),
        )

        tips = _normalize_tips(call_4, destination, month, days)

        return {
            "itinerary": itinerary_days,
            "hotels": hotels,
            "tips": {
                "hidden_gems": tips.get("hidden_gems", []),
                "warnings": tips.get("warnings", []),
                "must_eat": tips.get("must_eat", []),
                "cultural_tips": tips.get("cultural_tips", []),
                "packing_essentials": tips.get("packing_essentials", []),
                "budget_breakdown": tips.get("budget_breakdown", {}),
            },
        }
