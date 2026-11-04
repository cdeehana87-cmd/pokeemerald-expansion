# Run from the repo root:  python3 item_sources_report.py      (READ-ONLY)
# Counts where each evolution item can be found in the game data.
import re, os, sys, glob
def read(p): return open(p, encoding='utf-8', errors='replace').read()
if not os.path.isdir('data/maps') or not os.path.isdir('src'): sys.exit("STOP: run from the repo root")
ITEMS = ['LEAF_STONE','SUN_STONE','MOON_STONE','FIRE_STONE','WATER_STONE','THUNDER_STONE','DAWN_STONE','SHINY_STONE',
         'DUSK_STONE','ICE_STONE','DRAGON_SCALE','REAPER_CLOTH','PROTECTOR','UPGRADE','DUBIOUS_DISC','ELECTIRIZER','MAGMARIZER','METAL_COAT','KINGS_ROCK','LINKING_CORD']
SKIP = {'include/constants/items.h', 'src/data/items.h'}
cats = {i: {'map pickups': 0, 'shops/prizes': 0, 'gifts/other scripts': 0, 'C data': 0, 'wild held': 0, 'frlg maps only': 0} for i in ITEMS}
tok = {i: re.compile(r'\bITEM_' + i + r'\b') for i in ITEMS}
for p in glob.glob('data/**/*', recursive=True):
    if not os.path.isfile(p) or not p.endswith(('.json', '.inc')): continue
    frlg = 'frlg' in p.lower()
    for ln in read(p).split('\n'):
        for i in ITEMS:
            if not tok[i].search(ln): continue
            if frlg: cats[i]['frlg maps only'] += 1
            elif p.endswith('map.json'): cats[i]['map pickups'] += 1
            elif p.endswith('events.inc'): pass            # generated from map.json
            elif re.match(r'\s*\.2byte\s+ITEM_', ln) or 'setitemandprice' in ln: cats[i]['shops/prizes'] += 1
            else: cats[i]['gifts/other scripts'] += 1
for p in glob.glob('src/**/*.[ch]', recursive=True) + glob.glob('include/**/*.h', recursive=True):
    if p.replace(os.sep, '/') in SKIP: continue
    sp = 'species_info' in p
    for ln in read(p).split('\n'):
        if re.search(r'EVO_|CONDITIONS', ln) and not re.search(r'\.item(Common|Rare)', ln): continue   # skip the evolution definitions themselves
        for i in ITEMS:
            if tok[i].search(ln): cats[i]['wild held' if sp else 'C data'] += 1
print(f"{'item':15} {'maps':>5} {'shops':>6} {'scripts':>8} {'C data':>7} {'held':>5} {'frlg':>5}   verdict")
for i in ITEMS:
    c = cats[i]; real = c['map pickups'] + c['shops/prizes'] + c['gifts/other scripts'] + c['C data'] + c['wild held']
    print(f"{i:15} {c['map pickups']:5} {c['shops/prizes']:6} {c['gifts/other scripts']:8} {c['C data']:7} {c['wild held']:5} {c['frlg maps only']:5}   {'OK' if real else 'NO SOURCE'}")
print("\nNote: 'held' = wild Pokemon that may carry the item. Counts are lines in the data, not guaranteed reachable spots.")
