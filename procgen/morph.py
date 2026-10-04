"""Plant morph parameters — hybrid sine/shape description derived from phenotype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple, Union

from procgen.shapes import petals_for_shape

# Avoid hard dependency cycles for type checkers; Phenotype imported lazily in morph_from_phenotype


@dataclass
class MorphParams:
    """Enough data to draw one recognisable plant."""

    label: str = ""
    seed: int = 0

    # Stem (sine-first)
    height: float = 0.7
    stem_amp: float = 0.12
    stem_freq: float = 1.3
    stem_phase: float = 0.4
    stem_width: float = 0.55
    harmonics: Sequence[Tuple[float, float]] = field(default_factory=lambda: ((2.0, 0.22),))
    lean: float = 0.0
    stem_count: int = 1
    spiral: bool = False

    # Branching
    branch_count: int = 2
    branch_spread: float = 0.45

    # Leaves (hybrid)
    leaf_count: int = 6
    leaf_length: float = 0.55
    leaf_curl: float = 0.2
    feather: bool = False
    giant_leaves: bool = False

    # Flower (hybrid)
    flower_count: int = 1
    flower_radius: float = 0.55
    petals: int = 5
    petal_amp: float = 0.4
    colour: Tuple[int, int, int] = (210, 70, 90)
    leaf_colour: Tuple[int, int, int] = (55, 130, 70)
    stem_colour: Tuple[int, int, int] = (48, 105, 58)

    # Ornaments (simple shapes — intentionally not sine)
    glow: bool = False
    eyes: bool = False
    face: bool = False
    walking_roots: bool = False
    thunder: bool = False
    glass_stem: bool = False
    rainbow: bool = False

    # Growth scaling 0–1 (seedling → mature)
    progress: float = 1.0

    note: str = ""


def seed_from_plant_id(plant_id: str) -> int:
    """Stable deterministic seed from a plant id string."""
    # FNV-ish mix — independent of Python's randomized hash()
    h = 2166136261
    for ch in plant_id:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return int(h)


def _apply_mutations(m: MorphParams, mutations: List[str], branch: float) -> None:
    if "spiral_growth" in mutations:
        m.spiral = True
        m.stem_freq += 1.2
        m.stem_amp += 0.08
        m.harmonics = ((2.0, 0.35), (3.0, 0.2), (5.0, 0.12))
    if "multi_stem" in mutations:
        m.stem_count = 2 + int(branch * 2)
    if "giant_leaves" in mutations:
        m.giant_leaves = True
        m.leaf_length *= 1.45
        m.leaf_count = max(m.leaf_count, 5)
    if "feather_leaves" in mutations:
        m.feather = True
        m.leaf_colour = (70, 145, 95)
    if "dense_bloom" in mutations:
        m.flower_count = max(m.flower_count + 2, 4)
        m.petals = max(m.petals, 7)
    if "bioluminescence" in mutations:
        m.glow = True
        c = m.colour
        m.colour = (
            min(255, c[0] // 2 + 80),
            min(255, c[1] // 2 + 130),
            min(255, c[2] // 2 + 150),
        )
    if "eye_structures" in mutations:
        m.eyes = True
    if "face_bloom" in mutations:
        m.face = True
    if "walking_roots" in mutations:
        m.walking_roots = True
    if "glass_stem" in mutations:
        m.glass_stem = True
        m.stem_colour = (140, 200, 180)
        m.stem_width = max(0.25, m.stem_width * 0.75)
    if "thunder_bloom" in mutations:
        m.thunder = True
    if "rainbow_shift" in mutations:
        m.rainbow = True


def morph_from_traits(
    label: str,
    *,
    height: float = 0.7,
    branch: float = 0.45,
    leaf: float = 0.55,
    flower: float = 0.6,
    stem: float = 0.55,
    symmetry: float = 0.6,
    colour: Tuple[int, int, int] = (210, 70, 90),
    petals: int = 5,
    seed: int = 0,
    mutations: Optional[List[str]] = None,
    note: str = "",
    progress: float = 1.0,
    width: float = 0.55,
    disease: float = 0.55,
    stability: float = 0.55,
) -> MorphParams:
    """Trait → morph mapping used by preview gallery and phenotype bridge."""
    mutations = mutations or []
    chaos = max(0.0, 1.0 - symmetry)
    # Instability also adds harmonic complexity
    chaos = min(1.0, chaos + max(0.0, 0.55 - stability) * 0.5)

    g = max(40, int(80 + disease * 80))
    leaf_colour = (40, g, 50)

    m = MorphParams(
        label=label,
        seed=seed,
        height=height,
        stem_amp=0.06 + 0.22 * chaos + 0.08 * (1.0 - stem),
        stem_freq=0.9 + 1.4 * (0.3 + 0.7 * (1.0 - symmetry)),
        stem_phase=0.3 + (seed % 97) * 0.05,
        stem_width=max(0.2, 0.35 * stem + 0.25 * width),
        harmonics=((2.0, 0.15 + 0.25 * chaos), (3.0, 0.08 * chaos)),
        lean=((seed % 5) - 2) * 0.08 * (1.0 - symmetry),
        branch_count=1 + int(branch * 4),
        branch_spread=0.25 + branch * 0.5,
        leaf_count=3 + int(leaf * 6),
        leaf_length=0.35 + leaf * 0.45,
        leaf_curl=0.1 + chaos * 0.45,
        flower_count=max(1, int(flower * 3)),
        flower_radius=0.35 + flower * 0.45,
        petals=petals,
        petal_amp=0.25 + 0.35 * flower,
        colour=colour,
        leaf_colour=leaf_colour,
        progress=max(0.05, min(1.0, progress)),
        note=note,
    )
    _apply_mutations(m, mutations, branch)
    return m


def morph_from_phenotype(
    phenotype: Union[object, "Phenotype"],  # noqa: F821
    *,
    seed: int = 0,
    label: str = "",
    progress: float = 1.0,
) -> MorphParams:
    """Derive MorphParams from an expressed Phenotype (no save-data waves)."""
    ph = phenotype
    return morph_from_traits(
        label or "",
        height=float(ph.height),
        branch=float(ph.branch),
        leaf=float(ph.leaf),
        flower=float(ph.flower),
        stem=float(ph.stem),
        symmetry=float(ph.symmetry),
        colour=tuple(ph.colour_rgb),  # type: ignore[arg-type]
        petals=petals_for_shape(str(ph.shape_id)),
        seed=seed,
        mutations=list(ph.expressed_mutations),
        progress=progress,
        width=float(ph.width),
        disease=float(ph.disease),
        stability=float(ph.stability),
        note="",
    )


def demo_catalog() -> List[MorphParams]:
    """A small set of plants showing baseline + mutation looks."""
    return [
        morph_from_traits(
            "Common neat",
            height=0.55,
            branch=0.25,
            leaf=0.45,
            flower=0.5,
            stem=0.7,
            symmetry=0.85,
            colour=(220, 90, 110),
            petals=5,
            seed=11,
            note="Baseline — gentle sine stem, ordinary leaf/flower shapes",
        ),
        morph_from_traits(
            "Wavy tall",
            height=0.95,
            branch=0.55,
            leaf=0.5,
            flower=0.45,
            stem=0.45,
            symmetry=0.25,
            colour=(120, 80, 200),
            petals=6,
            seed=42,
            note="Low symmetry → stronger stem harmonics",
        ),
        morph_from_traits(
            "Spiral growth",
            height=0.8,
            branch=0.4,
            leaf=0.5,
            flower=0.55,
            stem=0.5,
            symmetry=0.35,
            colour=(230, 140, 50),
            petals=5,
            seed=7,
            mutations=["spiral_growth"],
            note="Mutation: wave-native spiral stem",
        ),
        morph_from_traits(
            "Multi + giant leaf",
            height=0.7,
            branch=0.75,
            leaf=0.85,
            flower=0.4,
            stem=0.65,
            symmetry=0.55,
            colour=(70, 160, 90),
            petals=4,
            seed=19,
            mutations=["multi_stem", "giant_leaves"],
            note="Multi-stem (sine) + giant leaves (hybrid scale)",
        ),
        morph_from_traits(
            "Feather + dense bloom",
            height=0.65,
            branch=0.5,
            leaf=0.7,
            flower=0.9,
            stem=0.55,
            symmetry=0.6,
            colour=(230, 100, 170),
            petals=8,
            seed=33,
            mutations=["feather_leaves", "dense_bloom"],
            note="Hybrid foliage/flowers — shapes with light edge wave",
        ),
        morph_from_traits(
            "Glow eyes",
            height=0.6,
            branch=0.35,
            leaf=0.4,
            flower=0.75,
            stem=0.5,
            symmetry=0.5,
            colour=(90, 140, 220),
            petals=6,
            seed=55,
            mutations=["bioluminescence", "eye_structures"],
            note="Ornaments stay simple circles (hard as pure sine)",
        ),
        morph_from_traits(
            "Face + legs",
            height=0.55,
            branch=0.3,
            leaf=0.35,
            flower=0.7,
            stem=0.6,
            symmetry=0.45,
            colour=(240, 200, 70),
            petals=5,
            seed=88,
            mutations=["face_bloom", "walking_roots"],
            note="Comedy mutations as readable icons, not waveforms",
        ),
        morph_from_traits(
            "Glass thunder",
            height=0.75,
            branch=0.4,
            leaf=0.45,
            flower=0.65,
            stem=0.4,
            symmetry=0.4,
            colour=(180, 90, 220),
            petals=7,
            seed=101,
            mutations=["glass_stem", "thunder_bloom", "rainbow_shift"],
            note="Colour/width tweaks + ring ornament",
        ),
        morph_from_traits(
            "Parent A",
            height=0.85,
            branch=0.3,
            leaf=0.4,
            flower=0.55,
            stem=0.7,
            symmetry=0.7,
            colour=(210, 55, 55),
            petals=5,
            seed=200,
            mutations=["spiral_growth"],
            note="Breeding demo parent",
        ),
        morph_from_traits(
            "Parent B",
            height=0.5,
            branch=0.7,
            leaf=0.75,
            flower=0.8,
            stem=0.5,
            symmetry=0.4,
            colour=(70, 120, 220),
            petals=8,
            seed=201,
            mutations=["dense_bloom", "feather_leaves"],
            note="Breeding demo parent",
        ),
        morph_from_traits(
            "Offspring",
            height=0.68,
            branch=0.5,
            leaf=0.58,
            flower=0.68,
            stem=0.6,
            symmetry=0.55,
            colour=(150, 80, 160),
            petals=6,
            seed=202,
            mutations=["spiral_growth", "feather_leaves"],
            note="Blend: spiral from A, feather from B, mixed colour",
        ),
    ]
