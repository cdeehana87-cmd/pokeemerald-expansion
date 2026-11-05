# Run from the repo root.
#   python3 add_stone_shop.py           -> DRY RUN
#   python3 add_stone_shop.py --apply   -> writes the change
# Fills the (now empty) Lilycove Dept Store 3F "Vitamins" shop with Dawn Stone and Shiny Stone.
import re, os, sys
STONES = ['ITEM_DAWN_STONE', 'ITEM_SHINY_STONE']
APPLY = '--apply' in sys.argv
P = 'data/maps/LilycoveCity_DepartmentStore_3F/scripts.inc'
def die(m): print("STOP:", m); sys.exit(1)
for f in (P, 'include/constants/items.h'):
    if not os.path.exists(f): die(f"{f} not found - run from the repo root")
items = open('include/constants/items.h', encoding='utf-8').read()
for s in STONES:
    if not re.search(r'\b' + s + r'\b', items): die(f"{s} does not exist in this fork's item list")
t = open(P, encoding='utf-8').read()
pat = re.compile(r'(LilycoveCity_DepartmentStore_3F_Pokemart_Vitamins:[ \t]*\n)([ \t]*)pokemartlistend')
ms = pat.findall(t)
if len(ms) != 1:
    if 'ITEM_DAWN_STONE' in t: die("already applied")
    die(f"the empty Vitamins shop list was not found exactly once (found {len(ms)}) - nothing was changed")
new = pat.sub(lambda m: m.group(1) + ''.join(f'{m.group(2)}.2byte {s}\n' for s in STONES) + m.group(2) + 'pokemartlistend', t)
print("Vitamins shop list before:  (empty)")
print("Vitamins shop list after:   " + ", ".join(STONES))
if APPLY:
    open(P, 'w', encoding='utf-8').write(new); print("\nAPPLIED. Now run:  make -j$(nproc)")
else:
    print("\nDRY RUN - nothing written. Add --apply to write it.")
