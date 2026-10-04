"""Pure plant genetics engine — no UI dependencies."""

from genetics.plant import Plant, create_seed_plant, breed
from genetics.phenotype import express_phenotype
from genetics.mutations import MUTATION_CATALOG

__all__ = [
    "Plant",
    "create_seed_plant",
    "breed",
    "express_phenotype",
    "MUTATION_CATALOG",
]
