# Run from the repo root:  python3 apply_guard_seed_patch.py
# 1) all outside writes to the EV/contest bytes are ignored (protects the packed points)
# 2) every newly created Pokemon is seeded with level-based points (enemy scaling)
import re, os, sys

def die(m): print("STOP:", m); sys.exit(1)
files = {}
for p in ('src/pokemon.c', 'src/attribute_points.c', 'include/attribute_points.h'):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
    files[p] = open(p, encoding='utf-8').read()
if 'gAttrWriteAllowed' in files['include/attribute_points.h']: die("already applied")
if 'ATTR_REF_LEVEL' not in files['include/attribute_points.h']: die("apply_nolevel_patch.py must be applied first")

def edit(p, name, pattern, repl, expect=1):
    new, n = re.subn(pattern, repl, files[p])
    if n != expect: die(f"'{name}' matched {n} places in {p} (expected {expect}) - nothing was changed")
    files[p] = new; print("ok:", name)

edit('include/attribute_points.h', 'header additions', r'#endif\s*$', lambda m: '''// Only attribute_points.c may write the EV/contest bytes; every other write is ignored.
extern bool8 gAttrWriteAllowed;

// New Pokemon start with level*level/ATTR_SEED_DIVISOR points in every attribute (enemy scaling).
#define ATTR_SEED_ENEMIES 1
#define ATTR_SEED_DIVISOR 25
void SeedAttrPoints(struct Pokemon *mon, u8 level);

#endif
''')
edit('src/attribute_points.c', 'write flag around stores',
     r'(\n)(\s*)for \(i = 0; i < PACK_BYTES; i\+\+\)\n(\s*)SetMonData\(mon, sByteFields\[i\], &buf\[i\]\);',
     lambda m: m.group(1) + m.group(2) + 'gAttrWriteAllowed = TRUE;\n' + m.group(2) + 'for (i = 0; i < PACK_BYTES; i++)\n' + m.group(3) + 'SetMonData(mon, sByteFields[i], &buf[i]);\n' + m.group(2) + 'gAttrWriteAllowed = FALSE;')
files['src/attribute_points.c'] += '''
bool8 gAttrWriteAllowed = FALSE;

void SeedAttrPoints(struct Pokemon *mon, u8 level)
{
    u16 bonus = ((u32)level * level) / ATTR_SEED_DIVISOR;
    u8 stat;
    for (stat = STAT_HP; stat <= STAT_SPDEF; stat++)
        SetAttrPoints(mon, stat, bonus);
}
'''
print("ok: seed function appended")
edit('src/pokemon.c', 'guard in SetBoxMonData',
     r'(void SetBoxMonData\(struct BoxPokemon \*boxMon, s32 field, const void \*dataArg\)\s*\{)',
     lambda m: m.group(1) + '''
    switch (field)
    {
    case MON_DATA_HP_EV: case MON_DATA_ATK_EV: case MON_DATA_DEF_EV:
    case MON_DATA_SPEED_EV: case MON_DATA_SPATK_EV: case MON_DATA_SPDEF_EV:
    case MON_DATA_COOL: case MON_DATA_BEAUTY: case MON_DATA_CUTE:
    case MON_DATA_SMART: case MON_DATA_TOUGH: case MON_DATA_SHEEN:
        if (!gAttrWriteAllowed)
            return; // these bytes now hold attribute points
        break;
    default:
        break;
    }
''')
edit('src/pokemon.c', 'seed new Pokemon in CreateMon',
     r'(CreateBoxMon\(&mon->box, species, level, personality, trainerId\);\s*\n\s*SetMonData\(mon, MON_DATA_LEVEL, &level\);)',
     lambda m: m.group(1) + '\n#if ATTR_SEED_ENEMIES\n    SeedAttrPoints(mon, level);\n#endif')
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
