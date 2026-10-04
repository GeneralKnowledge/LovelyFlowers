"""Specimen kinds — plants and the things that insist they are plants."""

from __future__ import annotations

from typing import Dict, Tuple


KIND_LABELS: Dict[str, str] = {
    "plant": "Plant",
    "fungus": "Fungus",
    "lichen": "Lichen",
    "mossbeast": "Mossbeast",
    "bloomcritter": "Bloomcritter",
    "hybrid": "Hybrid Abomination",
}


def hybrid_kind(kind_a: str, kind_b: str) -> str:
    if kind_a == kind_b and kind_a != "hybrid":
        return kind_a
    return "hybrid"


def can_cross(kind_a: str, kind_b: str) -> Tuple[bool, str]:
    if kind_a == "plant" and kind_b == "plant":
        return True, "Standard botanical cross."
    if "hybrid" in (kind_a, kind_b):
        return True, "Hybrid genetics are unstable. Radiation recommended. Or not."
    if kind_a != kind_b:
        return True, f"Cross-kingdom breeding: {kind_a} × {kind_b}. Taxonomy weeps."
    return True, "Ready."
