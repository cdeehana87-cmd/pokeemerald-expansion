# Run from the repo root:  python3 apply_trade_leftovers_patch.py
# Last three trade evolutions in the Hoenn Dex become level-up evolutions.
import re, os, sys
def die(m): print("STOP:", m); sys.exit(1)
G1 = 'src/data/pokemon/species_info/gen_1_families.h'
G3 = 'src/data/pokemon/species_info/gen_3_families.h'
for p in (G1, G3):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
files = {p: open(p, encoding='utf-8').read() for p in (G1, G3)}
if 'SPECIES_KINGDRA}' in files[G1] and 'EVO_LEVEL, 55, SPECIES_KINGDRA' in files[G1]: die("already applied")

def edit(p, name, target, lvl):
    pat = re.compile(r'\.evolutions = EVOLUTION\(\{EVO_TRADE, 0, SPECIES_' + target + r'\b.*?\}\),', re.S)
    ms = list(pat.finditer(files[p]))
    if len(ms) != 1: die(f"'{name}' matched {len(ms)} places (expected 1) - nothing was changed")
    block = ms[0].group(0)
    if len(block) > 400 or block.count('.evolutions') != 1: die(f"'{name}' matched an unexpectedly large block - nothing was changed")
    files[p] = files[p][:ms[0].start()] + f'.evolutions = EVOLUTION({{EVO_LEVEL, {lvl}, SPECIES_{target}}}),' + files[p][ms[0].end():]
    print(f"ok: {name} (was: {' '.join(block.split())[:90]}...)")

edit(G1, 'Seadra -> Kingdra at level 55', 'KINGDRA', 55)
edit(G1, 'Rhydon -> Rhyperior at level 65', 'RHYPERIOR', 65)
edit(G3, 'Dusclops -> Dusknoir at level 60', 'DUSKNOIR', 60)
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
