# Run from the repo root:  python3 apply_evolution_patch.py
# Trade evolutions in the Hoenn Dex become level-up evolutions; Feebas no longer depends on the (repurposed) Beauty stat.
import re, os, sys, glob
def die(m): print("STOP:", m); sys.exit(1)

G1 = 'src/data/pokemon/species_info/gen_1_families.h'
G3 = 'src/data/pokemon/species_info/gen_3_families.h'
for p in (G1, G3):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
files = {p: open(p, encoding='utf-8').read() for p in (G1, G3)}
if 'EVO_LEVEL, 40, SPECIES_ALAKAZAM' in files[G1]: die("already applied")
if not any('IF_GENDER' in open(f, encoding='utf-8').read() for f in glob.glob('src/data/pokemon/species_info/*.h')):
    die("this fork has no IF_GENDER evolution condition - tell Claude")

def edit(p, name, pattern, repl):
    new, n = re.subn(pattern, repl, files[p])
    if n != 1: die(f"'{name}' matched {n} places (expected 1) - nothing was changed")
    files[p] = new; print("ok:", name)

def trade_pair(sp, item='LINKING_CORD'):
    return (r'\.evolutions = EVOLUTION\(\{EVO_TRADE, 0, SPECIES_' + sp + r'\},\s*\n\s*\{EVO_ITEM, ITEM_' + item + r', SPECIES_' + sp + r'\}\),')

for sp, lvl in (('ALAKAZAM', 40), ('MACHAMP', 50), ('GOLEM', 50), ('GENGAR', 50)):
    edit(G1, f'{sp.title()} evolves at level {lvl}', trade_pair(sp), lambda m, sp=sp, lvl=lvl: f'.evolutions = EVOLUTION({{EVO_LEVEL, {lvl}, SPECIES_{sp}}}),')
edit(G3, 'Milotic at level 35 (no Beauty)',
     r'\.evolutions = EVOLUTION\(\{EVO_LEVEL, 0, SPECIES_MILOTIC, CONDITIONS\(\{IF_MIN_BEAUTY, 170\}\)\},\s*\n\s*\{EVO_TRADE, 0, SPECIES_MILOTIC, CONDITIONS\(\{IF_HOLD_ITEM, ITEM_PRISM_SCALE\}\)\},\s*\n\s*\{EVO_ITEM, ITEM_PRISM_SCALE, SPECIES_MILOTIC\}\),',
     lambda m: '.evolutions = EVOLUTION({EVO_LEVEL, 35, SPECIES_MILOTIC}),')
edit(G3, 'Huntail (male) / Gorebyss (female) at level 35',
     r'\.evolutions = EVOLUTION\(\{EVO_TRADE, 0, SPECIES_HUNTAIL, CONDITIONS\(\{IF_HOLD_ITEM, ITEM_DEEP_SEA_TOOTH\}\)\},\s*\n\s*\{EVO_TRADE, 0, SPECIES_GOREBYSS, CONDITIONS\(\{IF_HOLD_ITEM, ITEM_DEEP_SEA_SCALE\}\)\},\s*\n\s*\{EVO_ITEM, ITEM_DEEP_SEA_TOOTH, SPECIES_HUNTAIL\},\s*\n\s*\{EVO_ITEM, ITEM_DEEP_SEA_SCALE, SPECIES_GOREBYSS\}\),',
     lambda m: '.evolutions = EVOLUTION({EVO_LEVEL, 35, SPECIES_HUNTAIL, CONDITIONS({IF_GENDER, MON_MALE})},\n                                {EVO_LEVEL, 35, SPECIES_GOREBYSS, CONDITIONS({IF_GENDER, MON_FEMALE})}),')
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
