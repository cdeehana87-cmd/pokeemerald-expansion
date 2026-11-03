# Run from the repo root:  python3 apply_battle_patch.py
import re, os, sys
def die(m): print("STOP:", m); sys.exit(1)
for f, dst in (('attribute_points.c', 'src/attribute_points.c'), ('attribute_points.h', 'include/attribute_points.h')):
    if not os.path.exists(f): die(f"{f} not found in this folder - unzip the package here first")
    os.replace(f, dst)                      # overwrites the older copies
path = 'src/battle_script_commands.c'
text = open(path, encoding='utf-8').read()
if 'AwardBattlePoints' in text: die("battle_script_commands.c already patched")
call = r'MonGainEVs\(&gParties\[B_TRAINER_PLAYER\]\[\*expMonId\], faintedSpecies\);'
text, n = re.subn(call, 'AwardBattlePoints(&gParties[B_TRAINER_PLAYER][*expMonId]);', text)
if n != 2: die(f"found {n} MonGainEVs calls (expected 2) - nothing was changed")
text, n = re.subn(r'(#include "global\.h"\n)', lambda m: m.group(1) + '#include "attribute_points.h"\n', text, count=1)
if n != 1: die("could not add the include - nothing was changed")
open(path, 'w', encoding='utf-8').write(text)
print("ok: 2 call sites replaced, include added\nDONE. Now run:  make -j$(nproc)")
