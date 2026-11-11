# Run from the repo root.
#   python3 add_missing_wild.py            -> DRY RUN: shows exactly what would change
#   python3 add_missing_wild.py --apply    -> writes src/data/wild_encounters.json
# Puts each TARGET species in a few rare slots on maps that match its type (water = water/fishing, grass/bug = grass routes, ...).
import re, os, sys, json, random, glob

TARGETS = ['TREECKO', 'TORCHIC', 'MUDKIP', 'LILEEP', 'ANORITH']   # <- edit this list
PER_SPECIES = 3        # places per species
MAX_LEVEL = 30         # only slots at or below this level (these are first-stage Pokemon)
SEED = 7               # change to re-roll the random choices
APPLY = '--apply' in sys.argv
P = 'src/data/wild_encounters.json'
def die(m): print("STOP:", m); sys.exit(1)
def read(p): return open(p, encoding='utf-8', errors='replace').read()
if not os.path.exists(P): die(f"{P} not found - run from the repo root")

RATES = {'land_mons': [20,20,10,10,10,10,5,5,4,4,1,1], 'water_mons': [60,30,5,4,1], 'fishing_mons': [70,30,60,20,20,40,40,15,4,1]}
PREFER = {'land_mons': [8, 9, 6, 7], 'water_mons': [3, 2], 'fishing_mons': [8]}      # rare slots, most rare first (never the 1% ones)
ROUTES = r'MAP_ROUTE1(0[1-9]|[1-3]\d)$'
HABITAT = {   # primary type -> (fields to use, map-name pattern)
    'TYPE_WATER':    (['water_mons', 'fishing_mons'], ROUTES),
    'TYPE_GRASS':    (['land_mons'], r'MAP_(ROUTE(10[2-4]|11[0-9]|12[0-3])|PETALBURG_WOODS|SAFARI_ZONE_[A-Z]+)$'),
    'TYPE_BUG':      (['land_mons'], r'MAP_(ROUTE(10[2-4]|11[0-9]|12[0-3])|PETALBURG_WOODS|SAFARI_ZONE_[A-Z]+)$'),
    'TYPE_FIRE':     (['land_mons'], r'MAP_(ROUTE11[1-3]|FIERY_PATH|MT_CHIMNEY|JAGGED_PASS)'),
    'TYPE_ELECTRIC': (['land_mons'], r'MAP_(ROUTE1(10|18|13)|NEW_MAUVILLE)'),
    'TYPE_ROCK':     (['land_mons'], r'MAP_(GRANITE_CAVE|METEOR_FALLS|MT_PYRE|JAGGED_PASS|ROUTE11[13]|ROUTE11[0-9]_?)'),
}
for t in ('TYPE_GROUND', 'TYPE_FIGHTING', 'TYPE_STEEL'): HABITAT[t] = HABITAT['TYPE_ROCK']
for t in ('TYPE_GHOST', 'TYPE_DARK', 'TYPE_POISON'): HABITAT[t] = (['land_mons'], r'MAP_(MT_PYRE|ABANDONED_SHIP|ROUTE1(0[2-9]|[1-2]\d)$)')
DEFAULT = (['land_mons'], ROUTES)

# ---- primary type of each target (read from the species data)
types = {}
for p in glob.glob('src/data/pokemon/species_info/*.h'):
    t = read(p); heads = list(re.finditer(r'\[SPECIES_([A-Z0-9_]+)\]\s*=', t))
    for i, h in enumerate(heads):
        if h.group(1) in TARGETS and h.group(1) not in types:
            block = t[h.end(): heads[i+1].start() if i + 1 < len(heads) else len(t)]
            m = re.search(r'\.types\s*=\s*(?:MON_TYPES\(|\{)\s*(TYPE_[A-Z]+)', block)
            if m: types[h.group(1)] = m.group(1)
text = read(P); data = json.loads(text)

def entries(o):
    if isinstance(o, dict):
        if isinstance(o.get('map'), str) and any(f in o for f in RATES): yield o
        for v in o.values(): yield from entries(v)
    elif isinstance(o, list):
        for v in o: yield from entries(v)
by_map = {}
for e in entries(data):
    if 'FRLG' not in e['map'].upper(): by_map.setdefault(e['map'], []).append(e)
cnt = {}
for es in by_map.values():
    for e in es:
        for f in RATES:
            for m in (e.get(f) or {}).get('mons', []): cnt[m['species']] = cnt.get(m['species'], 0) + 1

rng = random.Random(SEED); used = set(); edits = []; summary = []
for sp in TARGETS:
    full = 'SPECIES_' + sp
    fields, pat = HABITAT.get(types.get(sp, ''), DEFAULT)
    cands = [(mp, f) for mp, es in by_map.items() if len(es) == 1 and re.search(pat, mp) for f in fields if f in es[0]]
    rng.shuffle(cands); got = 0
    print(f"\n{sp}  (type {types.get(sp, 'unknown -> default routes')}, {len(cands)} candidate spots)")
    for mp, f in cands:
        if got >= PER_SPECIES: break
        mons = by_map[mp][0][f]['mons']; rates = RATES[f]
        if len(mons) != len(rates) or any(m['species'] == full for m in mons): continue
        pick = next((i for i in PREFER[f] if (mp, f, i) not in used and mons[i]['max_level'] <= MAX_LEVEL and cnt.get(mons[i]['species'], 0) >= 3), None)
        if pick is None: continue
        old = mons[pick]; used.add((mp, f, pick)); cnt[old['species']] -= 1
        lv = f"Lv {old['min_level']}" + (f"-{old['max_level']}" if old['max_level'] != old['min_level'] else "")
        print(f"   {mp} [{f}] slot {pick+1} ({rates[pick]}% chance, {lv}): {old['species'][8:]} -> {sp}")
        edits.append((mp, f, pick, old['species'], full)); got += 1
    if got < PER_SPECIES: print(f"   NOTE: only {got} place(s) found for {sp}")

positions = []
for mp, f, pick, old, new in edits:
    mpos = text.index(f'"map": "{mp}"'); nxt = text.find('"map":', mpos + 1); nxt = len(text) if nxt < 0 else nxt
    fpos = text.index(f'"{f}"', mpos)
    if fpos > nxt: die(f"{mp}: text position check failed - nothing was changed")
    spots = list(re.finditer(r'"species":\s*"(SPECIES_[A-Z0-9_]+)"', text[fpos:nxt]))
    if len(spots) <= pick or spots[pick].group(1) != old: die(f"{mp}: text position check failed - nothing was changed")
    positions.append((fpos + spots[pick].start(1), fpos + spots[pick].end(1), new))
if APPLY:
    for a, b, new in sorted(positions, reverse=True): text = text[:a] + new + text[b:]
    json.loads(text); open(P, 'w', encoding='utf-8').write(text)
    print(f"\nAPPLIED {len(positions)} change(s). Now run:  make -j$(nproc)")
else:
    print(f"\nDRY RUN: {len(positions)} change(s) planned, nothing written. Add --apply to write them.")
