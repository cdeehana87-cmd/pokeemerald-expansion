# Run from the repo root:  python3 apply_allocation_patch.py
# Turns auto-spend OFF (points collect in a pool) and adds a Pokemon Center nurse menu to spend them.
import re, os, sys

def die(m): print("STOP:", m); sys.exit(1)
files = {}
for p in ('src/attribute_points.c', 'include/attribute_points.h', 'data/specials.inc', 'data/scripts/pkmn_center_nurse.inc'):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
    files[p] = open(p, encoding='utf-8').read()
if 'AttrPoints_Spend' in files['data/specials.inc']: die("already applied")
if 'gAttrGainPending' not in files['include/attribute_points.h']: die("apply_message_patch.py must be applied first")

def edit(p, name, pattern, repl, expect=1):
    new, n = re.subn(pattern, repl, files[p])
    if n != expect: die(f"'{name}' matched {n} places in {p} (expected {expect}) - nothing was changed")
    files[p] = new; print("ok:", name)

edit('include/attribute_points.h', 'auto-spend off', r'#define ATTR_PROTOTYPE_AUTOSPEND \d', lambda m: '#define ATTR_PROTOTYPE_AUTOSPEND 0')
edit('include/attribute_points.h', 'prototypes', r'#endif\s*$', lambda m: '''// Script specials used by the Pokemon Center nurse menu.
u16 AttrPoints_PartyHasPoints(void);
u16 AttrPoints_PrepareMon(void);
u16 AttrPoints_Spend(void);

#endif
''')
edit('src/attribute_points.c', 'includes', r'(#include "attribute_points\.h"\n)',
     lambda m: m.group(1) + '#include "constants/battle.h"\n#include "event_data.h"\n#include "string_util.h"\n')
files['src/attribute_points.c'] += '''
// ---- nurse menu specials (slot = VAR_0x8004, attribute = VAR_0x8005, amount choice = VAR_0x8006) ----
u16 AttrPoints_PartyHasPoints(void)
{
    u8 i, count = CalculatePlayerPartyCount();
    for (i = 0; i < count; i++)
        if (GetUnspentPoints(&gParties[B_TRAINER_PLAYER][i]) != 0)
            return TRUE;
    return FALSE;
}

// Puts the nickname in STR_VAR_1 and the unspent points in STR_VAR_2; returns the unspent points.
u16 AttrPoints_PrepareMon(void)
{
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][gSpecialVar_0x8004];
    u16 unspent = GetUnspentPoints(mon);
    GetMonData(mon, MON_DATA_NICKNAME, gStringVar1);
    gStringVar1[10] = EOS;
    ConvertIntToDecimalStringN(gStringVar2, unspent, STR_CONV_MODE_LEFT_ALIGN, 5);
    return unspent;
}

// Spends 1 / 5 / 10 / all points; returns the amount spent (0 = nothing happened).
// On success STR_VAR_2 = attribute name, STR_VAR_3 = amount.
u16 AttrPoints_Spend(void)
{
    static const u16 sAmounts[] = { 1, 5, 10, 65535 };
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][gSpecialVar_0x8004];
    u8 stat = gSpecialVar_0x8005;
    u16 amount, room, unspent = GetUnspentPoints(mon);

    if (stat > STAT_SPDEF)
        return 0;
    amount = sAmounts[gSpecialVar_0x8006 > 3 ? 0 : gSpecialVar_0x8006];
    room = AttrCap(stat) - GetAttrPoints(mon, stat);
    if (amount > unspent) amount = unspent;
    if (amount > room) amount = room;
    if (amount == 0 || !SpendAttrPoint(mon, stat, amount))
        return 0;
    StringCopy(gStringVar2, GetAttrName(stat));
    ConvertIntToDecimalStringN(gStringVar3, amount, STR_CONV_MODE_LEFT_ALIGN, 5);
    return amount;
}
'''
print("ok: C specials appended")
files['data/specials.inc'] = files['data/specials.inc'].rstrip('\n') + '\n  def_special AttrPoints_PartyHasPoints\n  def_special AttrPoints_PrepareMon\n  def_special AttrPoints_Spend\n'
print("ok: specials registered (appended at the end, so no existing special moves)")
edit('data/scripts/pkmn_center_nurse.inc', 'nurse entry point',
     r'(Common_EventScript_PkmnCenterNurse::\s*\n\s*lock\s*\n\s*faceplayer\s*\n)(\s*)setvar VAR_0x8004, 0',
     lambda m: m.group(1) + m.group(2) + 'goto AttrPoints_EventScript_Offer\n\nCommon_EventScript_PkmnCenterNurse_Main::\n' + m.group(2) + 'setvar VAR_0x8004, 0')
files['data/scripts/pkmn_center_nurse.inc'] = files['data/scripts/pkmn_center_nurse.inc'].rstrip('\n') + '''

@ ---- Attribute point allocation (only offered when someone in the party has unspent points) ----
AttrPoints_EventScript_Offer::
	specialvar VAR_RESULT, AttrPoints_PartyHasPoints
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_PkmnCenterNurse_Main
	msgbox AttrPoints_Text_Offer, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, AttrPoints_EventScript_ChooseMon
	goto Common_EventScript_PkmnCenterNurse_Main

AttrPoints_EventScript_ChooseMon::
	msgbox AttrPoints_Text_WhichMon, MSGBOX_DEFAULT
	special ChoosePartyMon
	waitstate
	goto_if_eq VAR_0x8004, 255, AttrPoints_EventScript_Done
AttrPoints_EventScript_ShowMon::
	specialvar VAR_RESULT, AttrPoints_PrepareMon
	goto_if_eq VAR_RESULT, 0, AttrPoints_EventScript_NoPoints
	message AttrPoints_Text_HasPoints
	waitmessage
	dynmultipush AttrPoints_Text_HP, 0
	dynmultipush AttrPoints_Text_Attack, 1
	dynmultipush AttrPoints_Text_Defense, 2
	dynmultipush AttrPoints_Text_Speed, 3
	dynmultipush AttrPoints_Text_SpAtk, 4
	dynmultipush AttrPoints_Text_SpDef, 5
	dynmultipush AttrPoints_Text_Back, 6
	dynmultistack 0, 0, FALSE, 7, FALSE, 0, DYN_MULTICHOICE_CB_NONE
	closemessage
	goto_if_ge VAR_RESULT, 6, AttrPoints_EventScript_ChooseMon
	copyvar VAR_0x8005, VAR_RESULT
	message AttrPoints_Text_HowMany
	waitmessage
	dynmultipush AttrPoints_Text_One, 0
	dynmultipush AttrPoints_Text_Five, 1
	dynmultipush AttrPoints_Text_Ten, 2
	dynmultipush AttrPoints_Text_All, 3
	dynmultipush AttrPoints_Text_Back, 4
	dynmultistack 0, 0, FALSE, 5, FALSE, 0, DYN_MULTICHOICE_CB_NONE
	closemessage
	goto_if_ge VAR_RESULT, 4, AttrPoints_EventScript_ShowMon
	copyvar VAR_0x8006, VAR_RESULT
	specialvar VAR_RESULT, AttrPoints_Spend
	goto_if_eq VAR_RESULT, 0, AttrPoints_EventScript_AtCap
	msgbox AttrPoints_Text_Spent, MSGBOX_DEFAULT
	goto AttrPoints_EventScript_ShowMon

AttrPoints_EventScript_NoPoints::
	msgbox AttrPoints_Text_NoPoints, MSGBOX_DEFAULT
	goto AttrPoints_EventScript_ChooseMon

AttrPoints_EventScript_AtCap::
	msgbox AttrPoints_Text_AtCap, MSGBOX_DEFAULT
	goto AttrPoints_EventScript_ShowMon

AttrPoints_EventScript_Done::
	goto Common_EventScript_PkmnCenterNurse_Main

AttrPoints_Text_Offer:
	.string "Would you like to spend attribute\\n"
	.string "points earned in battle?$"

AttrPoints_Text_WhichMon:
	.string "Which party member should receive\\n"
	.string "the points?$"

AttrPoints_Text_HasPoints:
	.string "{STR_VAR_1} has {STR_VAR_2} unspent\\n"
	.string "points. Which attribute should rise?$"

AttrPoints_Text_HowMany:
	.string "How many points?$"

AttrPoints_Text_Spent:
	.string "{STR_VAR_1}'s {STR_VAR_2} rose by\\n"
	.string "{STR_VAR_3}!$"

AttrPoints_Text_NoPoints:
	.string "{STR_VAR_1} has no unspent points.$"

AttrPoints_Text_AtCap:
	.string "That attribute cannot go any higher.$"

AttrPoints_Text_HP:
	.string "HP$"

AttrPoints_Text_Attack:
	.string "ATTACK$"

AttrPoints_Text_Defense:
	.string "DEFENSE$"

AttrPoints_Text_Speed:
	.string "SPEED$"

AttrPoints_Text_SpAtk:
	.string "SP. ATK$"

AttrPoints_Text_SpDef:
	.string "SP. DEF$"

AttrPoints_Text_One:
	.string "1$"

AttrPoints_Text_Five:
	.string "5$"

AttrPoints_Text_Ten:
	.string "10$"

AttrPoints_Text_All:
	.string "ALL$"

AttrPoints_Text_Back:
	.string "BACK$"
'''
print("ok: nurse menu script and text appended")
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
