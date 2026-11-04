# Run from the repo root:  python3 apply_summary_points_patch.py
# The summary screen's "EV" view will show your attribute points instead of (now meaningless) EVs.
import re, os, sys
def die(m): print("STOP:", m); sys.exit(1)
p = 'src/pokemon_summary_screen.c'
if not os.path.exists(p): die(f"{p} not found - run from the repo root")
t = open(p, encoding='utf-8').read()
if 'GetAttrPoints' in t: die("already applied")
t, n = re.subn(r'void ExtractMonSkillEvData\(struct Pokemon \*mon, struct PokeSummary \*sum\)\s*\{[^{}]*\}',
'''void ExtractMonSkillEvData(struct Pokemon *mon, struct PokeSummary *sum)
{
    // EV view now shows attribute points
    sum->currentHP = GetAttrPoints(mon, STAT_HP);
    sum->atk = GetAttrPoints(mon, STAT_ATK);
    sum->def = GetAttrPoints(mon, STAT_DEF);
    sum->spatk = GetAttrPoints(mon, STAT_SPATK);
    sum->spdef = GetAttrPoints(mon, STAT_SPDEF);
    sum->speed = GetAttrPoints(mon, STAT_SPEED);
}''', t)
if n != 1: die(f"ExtractMonSkillEvData matched {n} places (expected 1) - nothing was changed")
print("ok: EV view now reads attribute points")
t, n = re.subn(r'(#include "global\.h"\n)', lambda m: m.group(1) + '#include "attribute_points.h"\n', t, count=1)
if n != 1: die("could not add the include - nothing was changed")
print("ok: include added")
open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
