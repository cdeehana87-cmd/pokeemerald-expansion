# Run from the repo root.
#   python3 add_more_stones.py           -> DRY RUN
#   python3 add_more_stones.py --apply   -> writes the change
# Adds Fire, Water, Thunder, Leaf, Sun and Moon Stone to the Lilycove Dept Store 3F stone shop (which already sells Dawn/Shiny).
import re, os, sys
NEW = ['ITEM_FIRE_STONE', 'ITEM_WATER_STONE', 'ITEM_THUNDER_STONE', 'ITEM_LEAF_STONE', 'ITEM_SUN_STONE', 'ITEM_MOON_STONE']
APPLY = '--apply' in sys.argv
P = 'data/maps/LilycoveCity_DepartmentStore_3F/scripts.inc'
def die(m): print("STOP:", m); sys.exit(1)
for f in (P, 'include/constants/items.h'):
    if not os.path.exists(f): die(f"{f} not found - run from the repo root")
items = open('include/constants/items.h', encoding='utf-8').read()
for s in NEW:
    if not re.search(r'\b' + s + r'\b', items): die(f"{s} does not exist in this fork's item list")
t = open(P, encoding='utf-8').read()
pat = re.compile(r'(LilycoveCity_DepartmentStore_3F_Pokemart_Vitamins:[ \t]*\n)((?:[ \t]*\.2byte ITEM_[A-Z0-9_]+[ \t]*\n)*)([ \t]*)pokemartlistend')
ms = list(pat.finditer(t))
if len(ms) != 1: die(f"the stone shop list was not found exactly once (found {len(ms)}) - nothing was changed")
current = re.findall(r'ITEM_[A-Z0-9_]+', ms[0].group(2))
if 'ITEM_DAWN_STONE' not in current: die("the shop does not contain the Dawn Stone yet - run add_stone_shop.py --apply first")
todo = [s for s in NEW if s not in current]
if not todo: die("already applied")
ind = ms[0].group(3)
new = pat.sub(lambda m: m.group(1) + ''.join(f'{ind}.2byte {s}\n' for s in todo) + m.group(2) + m.group(3) + 'pokemartlistend', t)
print("shop before: " + ", ".join(current))
print("shop after:  " + ", ".join(todo + current))
if APPLY:
    open(P, 'w', encoding='utf-8').write(new); print("\nAPPLIED. Now run:  make -j$(nproc)")
else:
    print("\nDRY RUN - nothing written. Add --apply to write it.")
