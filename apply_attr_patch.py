# Run from the repo root (the folder that contains src/ and include/):  python3 apply_attr_patch.py
import re, os, shutil, sys

def die(msg):
    print("STOP:", msg); sys.exit(1)

if os.path.exists('attribute_points.c'): shutil.move('attribute_points.c', 'src/attribute_points.c')
if os.path.exists('attribute_points.h'): shutil.move('attribute_points.h', 'include/attribute_points.h')
for p in ('src/attribute_points.c', 'include/attribute_points.h'):
    if not os.path.exists(p): die(f"{p} is missing - unzip the package in the repo root first")

path = 'src/pokemon.c'
text = open(path, encoding='utf-8').read()
if 'attribute_points.h' in text: die("src/pokemon.c already patched")

def edit(name, pattern, fn):
    global text
    new, n = re.subn(pattern, fn, text)
    if n != 1: die(f"edit '{name}' matched {n} places (expected 1) - nothing was changed")
    text = new
    print("ok:", name)

edit("include", r'(#include "global\.h"\n)', lambda m: m.group(1) + '#include "attribute_points.h"\n')
edit("stat formula",
     r'(s32 n = \(\(\(2 \* baseStat \+ iv\[i\]) \+ ev\[i\] / 4(\) \* level\) / 100\) \+ 5;\s*\n(\s*)n = ModifyStatByNature\(nature, n, i\);)',
     lambda m: m.group(1) + m.group(2) + '\n' + m.group(3) + 'n += GetAttrPoints(mon, i);')
edit("HP formula",
     r'newMaxHP = \(\(\(n \+ ev\[STAT_HP\] / 4\) \* level\) / 100\) \+ level \+ 10;',
     lambda m: 'newMaxHP = (((n) * level) / 100) + level + 10 + GetAttrPoints(mon, STAT_HP);')
edit("disable EV gain",
     r'(void MonGainEVs\(struct Pokemon \*mon, enum Species defeatedSpecies\)\s*\{)',
     lambda m: m.group(1) + '\n    return; // attribute points replace EV gain')

open(path, 'w', encoding='utf-8').write(text)
print("DONE. Now run:  make -j$(nproc)")
