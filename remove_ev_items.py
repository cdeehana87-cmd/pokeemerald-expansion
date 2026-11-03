# Run from the repo root.
#   python3 remove_ev_items.py                 -> DRY RUN (changes nothing, prints what it would do)
#   python3 remove_ev_items.py --apply         -> apply, replacing map pickups with ITEM_NUGGET
#   python3 remove_ev_items.py --apply ITEM_X  -> apply with a different replacement item
import re, os, sys, glob

EV_ITEMS = [
 'HP_UP','PROTEIN','IRON','CARBOS','CALCIUM','ZINC',
 'HEALTH_WING','MUSCLE_WING','RESIST_WING','GENIUS_WING','CLEVER_WING','SWIFT_WING',
 'HEALTH_FEATHER','MUSCLE_FEATHER','RESIST_FEATHER','GENIUS_FEATHER','CLEVER_FEATHER','SWIFT_FEATHER',
 'MACHO_BRACE','POWER_WEIGHT','POWER_BRACER','POWER_BELT','POWER_LENS','POWER_BAND','POWER_ANKLET',
 'POMEG_BERRY','KELPSY_BERRY','QUALOT_BERRY','HONDEW_BERRY','GREPA_BERRY','TAMATO_BERRY',
]
APPLY = '--apply' in sys.argv
REPL = next((a for a in sys.argv[1:] if a.startswith('ITEM_')), 'ITEM_NUGGET')
tok = re.compile(r'\bITEM_(?:' + '|'.join(EV_ITEMS) + r')\b')
mart_line = re.compile(r'^\s*\.2byte\s+ITEM_(?:' + '|'.join(EV_ITEMS) + r')\s*$')
SKIP = {'include/constants/items.h', 'src/data/items.h'}   # item definitions are left alone on purpose

if not os.path.isdir('data/maps') or not os.path.isdir('src'): sys.exit("STOP: run from the repo root")
changed, report = {}, []

def read(p): return open(p, encoding='utf-8', errors='surrogateescape').read()

for p in sorted(glob.glob('data/maps/*/map.json') + glob.glob('data/maps/*/events.inc')):
    t = read(p); n = len(tok.findall(t))
    if n: changed[p] = (tok.sub(REPL, t), f"{n} replaced")
for p in sorted(glob.glob('data/maps/*/scripts.inc')):
    lines = read(p).split('\n'); out = []; dele = rep = 0
    for ln in lines:
        if mart_line.match(ln): dele += 1; continue
        if tok.search(ln):
            rep += 1; report.append(f"{p}: {ln.strip()}  -> (token replaced)"); ln = tok.sub(REPL, ln)
        out.append(ln)
    if dele or rep: changed[p] = ('\n'.join(out), f"{dele} shop lines deleted, {rep} other lines replaced")
for root in ('src', 'include'):
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f).replace(os.sep, '/')
            if p in SKIP or not f.endswith(('.c', '.h')): continue
            for i, ln in enumerate(read(p).split('\n'), 1):
                if tok.search(ln): report.append(f"{p}:{i}: {ln.strip()}   <- NOT changed (needs manual handling)")

print(f"replacement item: {REPL}   mode: {'APPLY' if APPLY else 'DRY RUN'}")
for p, (_, msg) in changed.items(): print(f"  {p}: {msg}")
print(f"\n{len(report)} lines need a look (script lines replaced, or code/data left for manual handling):")
for r in report: print("  " + r)
if APPLY:
    for p, (t, _) in changed.items(): open(p, 'w', encoding='utf-8', errors='surrogateescape').write(t)
    print("\nAPPLIED. Remaining items above must be handled by hand, then run: make -j$(nproc)")
else:
    print("\nDry run only - nothing was changed. Add --apply to write the changes.")
