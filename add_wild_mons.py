# Run from the repo root.
#   python3 add_wild_mons.py            -> DRY RUN: shows exactly what would change
#   python3 add_wild_mons.py --apply    -> writes the change to src/data/wild_encounters.json
# Puts each missing species into one grass/cave ("land") slot of one map. Levels of the replaced slot are kept.
import re, os, sys, json

PLAN = [   # (map, new species)  <- edit this list to place Pokemon elsewhere
    ('MAP_ROUTE102',            'SPECIES_SURSKIT'),
    ('MAP_ROUTE117',            'SPECIES_ROSELIA'),
    ('MAP_ROUTE114',            'SPECIES_ZANGOOSE'),
    ('MAP_GRANITE_CAVE_1F',     'SPECIES_MEDITITE'),
    ('MAP_METEOR_FALLS_1F_1R',  'SPECIES_LUNATONE'),
]
RATES = [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]   # chance (%) of each of the 12 land slots
APPLY = '--apply' in sys.argv
P = 'src/data/wild_encounters.json'
def die(m): print("STOP:", m); sys.exit(1)
if not os.path.exists(P): die(f"{P} not found - run from the repo root")
text = open(P, encoding='utf-8').read()
data = json.loads(text)

def entries(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get('map'), str) and 'land_mons' in obj: yield obj
        for v in obj.values(): yield from entries(v)
    elif isinstance(obj, list):
        for v in obj: yield from entries(v)
by_map = {}
for e in entries(data): by_map.setdefault(e['map'], []).append(e)

changes = []   # (text position of the species string, old, new)
for mp, new in PLAN:
    es = by_map.get(mp, [])
    if len(es) != 1: print(f"SKIP {mp}: found {len(es)} land-encounter entries (need exactly 1)"); continue
    mons = es[0]['land_mons']['mons']
    if len(mons) != 12: print(f"SKIP {mp}: has {len(mons)} land slots (expected 12)"); continue
    if any(m['species'] == new for m in mons): print(f"SKIP {mp}: {new} is already there"); continue
    counts = {}
    for m in mons: counts[m['species']] = counts.get(m['species'], 0) + 1
    order = sorted(range(12), key=lambda i: (RATES[i], -i))                     # lowest chance first
    pick = next((i for i in order if counts[mons[i]['species']] >= 2 and RATES[i] >= 5), None)
    note = ""
    if pick is None: pick = next((i for i in order if counts[mons[i]['species']] >= 2), order[0]); note = " (WARNING: low chance or removes the last copy of a species)"
    old = mons[pick]['species']
    # locate the same slot in the text: the pick-th "species" after this map's "land_mons"
    mpos = text.index(f'"map": "{mp}"'); lpos = text.index('"land_mons"', mpos)
    spots = [m for m in re.finditer(r'"species":\s*"(SPECIES_[A-Z0-9_]+)"', text[lpos:])][:12]
    if len(spots) < 12 or spots[pick].group(1) != old: die(f"{mp}: text position check failed - nothing was changed")
    a, b = lpos + spots[pick].start(1), lpos + spots[pick].end(1)
    changes.append((a, b, new))
    lv = f"Lv {mons[pick]['min_level']}" + (f"-{mons[pick]['max_level']}" if mons[pick]['max_level'] != mons[pick]['min_level'] else "")
    print(f"{mp}: slot {pick+1} ({RATES[pick]}% chance, {lv}): {old} -> {new}{note}")

if APPLY:
    for a, b, new in sorted(changes, reverse=True): text = text[:a] + new + text[b:]
    json.loads(text)    # must still be valid JSON
    open(P, 'w', encoding='utf-8').write(text)
    print(f"\nAPPLIED {len(changes)} change(s). Now run:  make -j$(nproc)")
else:
    print(f"\nDRY RUN: {len(changes)} change(s) planned, nothing written. Add --apply to write them.")
