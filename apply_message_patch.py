# Run from the repo root:  python3 apply_message_patch.py
# Shows "<Pokemon>'s <ATTRIBUTE> rose by N!" right after the EXP message.
import re, os, sys

def die(m): print("STOP:", m); sys.exit(1)
files = {}
for p in ('src/attribute_points.c', 'include/attribute_points.h', 'src/battle_script_commands.c',
          'include/constants/battle_string_ids.h', 'src/battle_message.c'):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
    files[p] = open(p, encoding='utf-8').read()
if 'gAttrGainPending' in files['include/attribute_points.h']: die("already applied")

def edit(p, name, pattern, repl, expect=1):
    new, n = re.subn(pattern, repl, files[p])
    if n != expect: die(f"'{name}' matched {n} places in {p} (expected {expect}) - nothing was changed")
    files[p] = new; print("ok:", name)

edit('include/attribute_points.h', 'header', r'#endif\s*$', lambda m: '''// Filled by AwardBattlePoints so the battle script can print a message.
extern bool8 gAttrGainPending;
extern u8 gAttrGainStat;       // STAT_* that gained, or 0xFF if the points went to the unspent pool
extern u16 gAttrGainAmount;
const u8 *GetAttrName(u8 stat);

#endif
''')
edit('src/attribute_points.c', 'record the gain',
     r'#if ATTR_PROTOTYPE_AUTOSPEND\n    if \(amount != 0\)\n        SpendAttrPoint\(mon, stat, amount\);[^\n]*\n#else\n    CalculateMonStats\(mon\);\n#endif',
     lambda m: '''#if ATTR_PROTOTYPE_AUTOSPEND
    if (amount != 0 && SpendAttrPoint(mon, stat, amount))
    {
        gAttrGainStat = stat;
        gAttrGainAmount = amount;
        gAttrGainPending = TRUE;
    }
#else
    CalculateMonStats(mon);
    gAttrGainStat = 0xFF;
    gAttrGainAmount = roll;
    gAttrGainPending = TRUE;
#endif''')
files['src/attribute_points.c'] += '''
bool8 gAttrGainPending = FALSE;
u8 gAttrGainStat = 0xFF;
u16 gAttrGainAmount = 0;

static const u8 sAttrNameHP[]    = _("HP");
static const u8 sAttrNameAtk[]   = _("ATTACK");
static const u8 sAttrNameDef[]   = _("DEFENSE");
static const u8 sAttrNameSpeed[] = _("SPEED");
static const u8 sAttrNameSpAtk[] = _("SP. ATK");
static const u8 sAttrNameSpDef[] = _("SP. DEF");
static const u8 *const sAttrNames[6] = { sAttrNameHP, sAttrNameAtk, sAttrNameDef, sAttrNameSpeed, sAttrNameSpAtk, sAttrNameSpDef };

const u8 *GetAttrName(u8 stat)
{
    return sAttrNames[stat > STAT_SPDEF ? 0 : stat];
}
'''
print("ok: globals and names appended")
edit('src/battle_script_commands.c', 'clear flag at start of state 2',
     r'(case 2: // set exp value to the poke in expgetter_id and print message\s*\n\s*if \(gBattleControllerExecFlags == 0\)\s*\n\s*\{)',
     lambda m: m.group(1) + '\n            gAttrGainPending = FALSE;')
edit('src/battle_script_commands.c', 'print message at start of state 3',
     r'(case 3: // Set stats and give exp\s*\n\s*if \(gBattleControllerExecFlags == 0\)\s*\n\s*\{)',
     lambda m: m.group(1) + '''
            if (gAttrGainPending)
            {
                gAttrGainPending = FALSE;
                PREPARE_MON_NICK_WITH_PREFIX_BUFFER(gBattleTextBuff1, 0, *expMonId);
                ConvertIntToDecimalStringN(gBattleTextBuff3, gAttrGainAmount, STR_CONV_MODE_LEFT_ALIGN, 3);
                if (gAttrGainStat != 0xFF)
                {
                    StringCopy(gBattleTextBuff2, GetAttrName(gAttrGainStat));
                    PrepareStringBattle(STRINGID_ATTRGAINED, 0);
                }
                else
                {
                    PrepareStringBattle(STRINGID_ATTRPOOLGAINED, 0);
                }
                break; // this state runs again once the message has finished
            }''')
edit('include/constants/battle_string_ids.h', 'string ids',
     r'(\n)(\s*)STRINGID_COUNT\b',
     lambda m: m.group(1) + m.group(2) + 'STRINGID_ATTRGAINED,\n' + m.group(2) + 'STRINGID_ATTRPOOLGAINED,\n' + m.group(2) + 'STRINGID_COUNT')
edit('src/battle_message.c', 'message text',
     r'(\[STRINGID_PKMNGREWTOLV\][^\n]*\n)',
     lambda m: m.group(1) + '''    [STRINGID_ATTRGAINED]                           = COMPOUND_STRING("{B_BUFF1}'s {B_BUFF2} rose by {B_BUFF3}!\\p"),
    [STRINGID_ATTRPOOLGAINED]                       = COMPOUND_STRING("{B_BUFF1} gained {B_BUFF3} attribute points!\\p"),
''')
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
