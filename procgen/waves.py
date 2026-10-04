"""Sine / harmonic curve sampling — the math under the plant body."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]


def harmonic_offset(
    t: float,
    amp: float,
    freq: float,
    phase: float,
    harmonics: Sequence[Tuple[float, float]] = (),
) -> float:
    """Lateral offset at normalised progress t in [0, 1]."""
    x = amp * math.sin(2 * math.pi * freq * t + phase)
    for mult, weight in harmonics:
        x += amp * weight * math.sin(2 * math.pi * freq * mult * t + phase * mult)
    return x


def sample_stem_curve(
    length: float,
    amp: float,
    freq: float,
    phase: float,
    harmonics: Sequence[Tuple[float, float]] = (),
    steps: int = 24,
    lean: float = 0.0,
) -> List[Point]:
    """Growth-axis curve with sine lateral displacement (not a graph plot)."""
    points: List[Point] = []
    for i in range(steps + 1):
        t = i / steps
        # Ease amplitude near soil so the plant feels rooted
        local_amp = amp * (0.15 + 0.85 * t)
        x = lean * t * length * 0.25 + harmonic_offset(t, local_amp, freq, phase, harmonics)
        y = -length * t
        points.append((x, y))
    return points


def sample_leaf_polygon(
    length: float,
    width: float,
    curl: float = 0.0,
    serration: float = 0.0,
    steps: int = 14,
) -> List[Point]:
    """Teardrop leaf: ordinary silhouette with optional sine edge deform."""
    pts: List[Point] = []
    # Outline along both sides from base to tip and back
    for i in range(steps + 1):
        t = i / steps
        # Width envelope peaks mid-leaf
        envelope = math.sin(math.pi * t) ** 0.85
        wave = 1.0 + serration * 0.25 * math.sin(t * math.pi * 5)
        x = width * 0.5 * envelope * wave
        y = -length * t
        x += curl * length * 0.15 * math.sin(math.pi * t)
        pts.append((x, y))
    for i in range(steps, -1, -1):
        t = i / steps
        envelope = math.sin(math.pi * t) ** 0.85
        wave = 1.0 + serration * 0.25 * math.sin(t * math.pi * 5 + 0.4)
        x = -width * 0.5 * envelope * wave
        y = -length * t
        x += curl * length * 0.15 * math.sin(math.pi * t)
        pts.append((x, y))
    return pts


def sample_petal_polygon(
    radius: float,
    petals: int,
    lobe_amp: float = 0.35,
    phase: float = 0.0,
    steps_per_petal: int = 8,
) -> List[Point]:
    """Closed flower outline via polar sine lobes — filled shape, not a plot."""
    petals = max(3, petals)
    total = petals * steps_per_petal
    pts: List[Point] = []
    # Keep a solid body so flowers never collapse into a thin ring
    base = 0.62
    amp = min(0.38, max(0.18, lobe_amp))
    for i in range(total):
        theta = (2 * math.pi * i) / total + phase
        r = radius * (base + amp * (0.5 + 0.5 * math.sin(petals * theta)))
        pts.append((r * math.cos(theta), -r * math.sin(theta)))
    return pts


def rotate_points(points: Iterable[Point], angle_rad: float) -> List[Point]:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return [(x * c - y * s, x * s + y * c) for x, y in points]


def translate_points(points: Iterable[Point], dx: float, dy: float) -> List[Point]:
    return [(x + dx, y + dy) for x, y in points]


def scale_points(points: Iterable[Point], sx: float, sy: float | None = None) -> List[Point]:
    if sy is None:
        sy = sx
    return [(x * sx, y * sy) for x, y in points]
