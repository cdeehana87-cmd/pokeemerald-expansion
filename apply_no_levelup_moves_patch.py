# Run from the repo root:  python3 apply_no_levelup_moves_patch.py
# Level-ups (battle, Rare Candy, daycare) no longer teach moves. Evolution-time moves and starting moves are untouched.
import re, os, sys
def die(m): print("STOP:", m); sys.exit(1)
PK, H, CFG = 'src/pokemon.c', 'include/attribute_points.h', 'include/config/summary_screen.h'
for p in (PK, H, CFG):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
files = {p: open(p, encoding='utf-8').read() for p in (PK, H, CFG)}
if 'ATTR_LEVELUP_LEARNING' in files[H]: die("already applied")
def edit(p, name, pattern, repl):
    new, n = re.subn(pattern, repl, files[p])
    if n != 1: die(f"'{name}' matched {n} places in {p} (expected 1) - nothing was changed")
    files[p] = new; print("ok:", name)
edit(H, 'switch in header', r'#endif\s*$', lambda m: '// 0 = leveling up (battle, Rare Candy, daycare) teaches no moves. Moves come from TMs and the gym posts.\n#define ATTR_LEVELUP_LEARNING 0\n\n#endif\n')
edit(PK, 'level-up learning off', r'(enum Move MonTryLearningNewMoveAtLevel\(struct Pokemon \*mon, bool32 firstMove, u32 level\)\s*\{)',
     lambda m: m.group(1) + '\n#if !ATTR_LEVELUP_LEARNING\n    return MOVE_NONE; // moves now come from TMs and gym posts\n#endif')
edit(CFG, 'summary-screen relearner off', r'(#define P_SUMMARY_SCREEN_MOVE_RELEARNER\s+)TRUE', lambda m: m.group(1) + 'FALSE')
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
