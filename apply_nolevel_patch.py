# Run from the repo root:  python3 apply_nolevel_patch.py
# 1) stats no longer depend on level, 2) damage formula no longer depends on level, 3) point roll becomes 1..3
import re, os, sys

def die(m): print("STOP:", m); sys.exit(1)

files = {}
def load(p):
    if not os.path.exists(p): die(f"{p} not found - run this from the repo root")
    files[p] = open(p, encoding='utf-8').read()

def edit(p, name, pattern, repl, expect):
    new, n = re.subn(pattern, repl, files[p])
    if n != expect: die(f"'{name}' matched {n} places in {p} (expected {expect}) - nothing was changed")
    files[p] = new; print("ok:", name)

for p in ('src/pokemon.c', 'src/battle_util.c', 'src/attribute_points.c', 'include/attribute_points.h'): load(p)
if 'ATTR_REF_LEVEL' in files['include/attribute_points.h']: die("already applied")
if 'attribute_points.h' not in files['src/pokemon.c']: die("run apply_attr_patch.py first")

edit('include/attribute_points.h', 'reference level', r'#endif\s*$',
     lambda m: '// Level used by the stat and damage formulas. Level no longer changes stats; only points do.\n#define ATTR_REF_LEVEL 50\n\n#endif\n', 1)
edit('src/pokemon.c', 'stat formula ignores level',
     r'(s32 n = \(\(\(2 \* baseStat \+ iv\[i\]\) \* )level(\) / 100\) \+ 5;)',
     lambda m: m.group(1) + 'ATTR_REF_LEVEL' + m.group(2), 1)
edit('src/pokemon.c', 'HP formula ignores level',
     r'newMaxHP = \(\(\(n\) \* level\) / 100\) \+ level \+ 10 \+ GetAttrPoints\(mon, STAT_HP\);',
     lambda m: 'newMaxHP = (((n) * ATTR_REF_LEVEL) / 100) + ATTR_REF_LEVEL + 10 + GetAttrPoints(mon, STAT_HP);', 1)
edit('src/battle_util.c', 'include', r'(#include "global\.h"\n)', lambda m: m.group(1) + '#include "attribute_points.h"\n', 1)
edit('src/battle_util.c', 'damage (battler level)', r'2 \* gBattleMons\[battlerAtk\]\.level / 5 \+ 2', lambda m: '2 * ATTR_REF_LEVEL / 5 + 2', 2)
edit('src/battle_util.c', 'damage (level variable)', r'\(2 \* level / 5 \+ 2\)', lambda m: '(2 * ATTR_REF_LEVEL / 5 + 2)', 1)
edit('src/battle_util.c', 'AI damage estimate', r'GetMonData\(&party\[partyIndex\], MON_DATA_LEVEL\) \* 2 / 5 \+ 2', lambda m: 'ATTR_REF_LEVEL * 2 / 5 + 2', 1)
edit('src/attribute_points.c', 'roll 1..3', r'1 \+ \(Random\(\) % 10\)', lambda m: '1 + (Random() % 3)', 1)

for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
