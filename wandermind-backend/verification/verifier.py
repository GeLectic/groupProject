import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from utils.groq_client import GroqClient


FACT_CATEGORIES = [
    "places_mentioned",
    "food_tips",
    "transport_tips",
    "hidden_gems",
    "warnings",
    "estimated_costs",
    "best_time_tips",
]


def _normalize_fact(fact: str) -> str:
    fact = fact.lower().strip()
    fact = re.sub(r"\s+", " ", fact)
    fact = re.sub(r"[^a-z0-9\s]", "", fact)
    return fact


def _flatten_strings(values: Any) -> List[str]:
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        out: List[str] = []
        for item in values:
            out.extend(_flatten_strings(item))
        return out
    if isinstance(values, dict):
        out: List[str] = []
        for item in values.values():
            out.extend(_flatten_strings(item))
        return out
    return []


async def run_verification(
    destination: str,
    metadata_store: List[Dict[str, Any]],
    groq_client: GroqClient,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    fact_sources: Dict[str, Set[str]] = defaultdict(set)
    fact_original: Dict[str, str] = {}
    entry_fact_map: Dict[int, Set[str]] = defaultdict(set)
    all_extracted_facts: Dict[str, List[str]] = defaultdict(list)

    for idx, entry in enumerate(metadata_store):
        extracted = entry.get("extracted_facts") or {}
        source = entry.get("source", "")

        for category in FACT_CATEGORIES:
            facts = extracted.get(category, []) if isinstance(extracted, dict) else []
            for fact in facts:
                if not isinstance(fact, str) or len(fact.strip()) < 3:
                    continue
                norm = _normalize_fact(fact)
                if not norm:
                    continue
                fact_sources[norm].add(source)
                fact_original.setdefault(norm, fact)
                entry_fact_map[idx].add(norm)
                all_extracted_facts[category].append(fact)

    high_confidence: List[str] = []
    low_confidence: List[str] = []

    if groq_client.enabled and all_extracted_facts:
        try:
            consensus = await groq_client.json_chat(
                system_prompt="You are a travel fact verification assistant.",
                user_prompt=(
                    f"From these traveler-reported facts about {destination}, identify claims "
                    "that appear in multiple sources (high confidence) vs single sources (low confidence). "
                    f"Facts: {json.dumps(all_extracted_facts)[:12000]} "
                    "Return JSON: { high_confidence: [...], low_confidence: [...] }"
                ),
            )
            high_confidence = _flatten_strings(consensus.get("high_confidence", []))
            low_confidence = _flatten_strings(consensus.get("low_confidence", []))
        except Exception:
            high_confidence = []
            low_confidence = []

    if not high_confidence and not low_confidence:
        for norm, sources in fact_sources.items():
            if len(sources) >= 2:
                high_confidence.append(fact_original.get(norm, norm))
            else:
                low_confidence.append(fact_original.get(norm, norm))

    high_norms = {_normalize_fact(item) for item in high_confidence if item}
    low_norms = {_normalize_fact(item) for item in low_confidence if item}

    conflicts_list: List[Dict[str, Any]] = []
    if groq_client.enabled and high_confidence:
        try:
            conflict_payload = await groq_client.json_chat(
                system_prompt="You are a travel information conflict detector.",
                user_prompt=(
                    f"Identify any contradicting claims in this set of travel facts about {destination}. "
                    "For each conflict, note both sides and which seems more credible. "
                    f"Facts: {json.dumps(high_confidence)[:10000]} "
                    "Return JSON: { conflicts: [{topic, claim_a, claim_b, likely_true}] }"
                ),
            )
            raw_conflicts = conflict_payload.get("conflicts", [])
            if isinstance(raw_conflicts, list):
                conflicts_list = [c for c in raw_conflicts if isinstance(c, dict)]
        except Exception:
            conflicts_list = []

    conflict_fact_norms: Set[str] = set()
    for conflict in conflicts_list:
        conflict_fact_norms.add(_normalize_fact(str(conflict.get("claim_a", ""))))
        conflict_fact_norms.add(_normalize_fact(str(conflict.get("claim_b", ""))))

    base_scores = {"youtube": 0.75, "reddit": 0.80, "quora": 0.65}

    for idx, entry in enumerate(metadata_store):
        source = entry.get("source", "")
        score = base_scores.get(source, 0.60)
        facts = entry_fact_map.get(idx, set())

        two_plus = any(len(fact_sources.get(f, set())) >= 2 for f in facts)
        three_plus = any(len(fact_sources.get(f, set())) >= 3 for f in facts)

        if three_plus:
            score += 0.15
        elif two_plus:
            score += 0.10

        if any(f in conflict_fact_norms for f in facts):
            score -= 0.20

        entry["confidence"] = max(0.0, min(1.0, round(score, 2)))

        if any(f in high_norms for f in facts):
            entry["consensus_score"] = "high"
        elif any(f in low_norms for f in facts):
            entry["consensus_score"] = "low"
        else:
            entry["consensus_score"] = "single"

    return metadata_store, conflicts_list
