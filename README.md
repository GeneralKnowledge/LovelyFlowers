# Lovely Flowers

A small single-player plant breeding and collection game.

**Collect → forage → breed → irradiate → trial → compete → sell → repeat.**

Inspired by the simple outer loop of [Horsey Game](https://store.steampowered.com/app/3602570/Horsey_Game/) (Captain Games), translated into plants — with a genetics engine taken far too seriously.

## Play

```bash
pip install -r requirements.txt
python main.py
```

| Control | Action |
|---|---|
| Greenhouse | Pots & specimens |
| Shop | Seeds & upgrades |
| Travel | Simulated expeditions (wild finds) |
| Lab | Radiation chamber |
| Breed | Normal or irradiated crosses |
| Compete / Trial Shows | Big shows + cheap keep-vs-sell grades |
| Catalog | Discoveries (`???` until found) |
| Space / Wait | Advance time |
| S | Save · H Help · Esc back/quit · Ctrl+N new |

Saves to `data/save.json`.

## Horsey-inspired systems

- **Wild foraging** — expedition locations (Meadow, Fungal Hollow, Radiation Flats, Scrapyard Bog, Abandoned Lab). Travel is simulated for now; real movement comes later.
- **Non-plants** — fungi, lichen, mossbeasts, bloomcritters; cross-kingdom breeding yields unstable hybrids.
- **Radiation chamber** — unlock via Abandoned Lab or shop kit; force mutations (mild/standard/severe). Irradiated crosses on the breed bench.
- **Trial shows** — cheap graded evaluations (keep vs sell), like test races.
- **Competitions** — People’s Pot through Botanical Abomination for money & prestige.

## Genetics

Diploid alleles, dominance/recessives, hidden carriers, trade-offs, heritable mutations. Engine lives in `genetics/` and is testable without Pygame.

```bash
python simulate.py --lineage 15 --seed 7
pytest -q
```

## Layout

```
genetics/     # alleles, mutations, phenotype, kinds
game/         # state, world/locations, wild, radiation, competitions
ui/           # Pygame front-end + procedural renderer
tests/
main.py
```
