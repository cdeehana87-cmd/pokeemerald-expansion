# Run from the repo root.
#   python3 add_jirachi_gift.py           -> DRY RUN (checks everything, writes nothing)
#   python3 add_jirachi_gift.py --apply   -> writes the change
# Mossdeep Space Center 1F scientist gives a Lv 5 Jirachi once, after the National Dex is enabled.
import re, os, sys, glob
APPLY = '--apply' in sys.argv
def die(m): print("STOP:", m); sys.exit(1)
def read(p): return open(p, encoding='utf-8', errors='replace').read()

MAP = 'data/maps/MossdeepCity_SpaceCenter_1F/scripts.inc'
FLAGS = 'include/constants/flags.h'
for p in (MAP, FLAGS):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
blob = "\n".join(read(p) for p in glob.glob('data/**/*.inc', recursive=True) + glob.glob('src/*.c') + glob.glob('include/**/*.h', recursive=True))
needed = ['Common_EventScript_TransferredToPC::', 'Common_EventScript_NameReceivedPartyMon::', 'Common_EventScript_NameReceivedBoxMon::',
          'Common_EventScript_GetGiftMonPartySlot::', 'Common_EventScript_NoMoreRoomForPokemon::', 'gText_NicknameThisPokemon', 'MUS_OBTAIN_ITEM', 'FLAG_SYS_NATIONAL_DEX']
missing = [n for n in needed if n not in blob]
if missing: die("these names were not found in this fork, tell Claude: " + ", ".join(missing))

m = read(MAP); f = read(FLAGS)
if 'FLAG_RECEIVED_JIRACHI' in f or 'JirachiCheck' in m: die("already applied")
if len(re.findall(r'FLAG_UNUSED_0x020\b', blob)) != 1: die("FLAG_UNUSED_0x020 is used somewhere else - tell Claude")

hook = re.compile(r'(MossdeepCity_SpaceCenter_1F_EventScript_Scientist::[ \t]*\n[ \t]*lock[ \t]*\n[ \t]*faceplayer[ \t]*\n[ \t]*goto_if_eq VAR_MOSSDEEP_CITY_STATE, 2, MossdeepCity_SpaceCenter_1F_EventScript_ScientistMagma[ \t]*\n)([ \t]*)(msgbox MossdeepCity_SpaceCenter_1F_Text_RocketLaunchDemandsPerfection)')
if len(hook.findall(m)) != 1: die("could not find the Scientist script exactly once - nothing was changed")
flagdef = re.compile(r'#define FLAG_UNUSED_0x020[ \t]+0x20 // Unused Flag')
if len(flagdef.findall(f)) != 1: die("could not find the FLAG_UNUSED_0x020 definition exactly once - nothing was changed")

P = 'MossdeepCity_SpaceCenter_1F_EventScript_Jirachi'
m = hook.sub(lambda x: x.group(1) + x.group(2) + 'goto_if_set FLAG_SYS_NATIONAL_DEX, ' + P + 'Check\n' + x.group(2) + x.group(3), m)
f = flagdef.sub('#define FLAG_RECEIVED_JIRACHI 0x20 // Received Jirachi at the Mossdeep Space Center', f)
m = m.rstrip('\n') + f'''

{P}Check::
	goto_if_set FLAG_RECEIVED_JIRACHI, {P}Already
	msgbox MossdeepCity_SpaceCenter_1F_Text_JirachiOffer, MSGBOX_DEFAULT
	setvar VAR_TEMP_TRANSFERRED_SPECIES, SPECIES_JIRACHI
	givemon SPECIES_JIRACHI, 5
	goto_if_eq VAR_RESULT, MON_GIVEN_TO_PARTY, {P}Party
	goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC, {P}PC
	goto Common_EventScript_NoMoreRoomForPokemon
	end

{P}Party::
	call {P}Fanfare
	msgbox gText_NicknameThisPokemon, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, {P}Done
	call Common_EventScript_GetGiftMonPartySlot
	call Common_EventScript_NameReceivedPartyMon
	goto {P}Done
	end

{P}PC::
	call {P}Fanfare
	msgbox gText_NicknameThisPokemon, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, {P}ToPC
	call Common_EventScript_NameReceivedBoxMon
	goto {P}ToPC
	end

{P}ToPC::
	call Common_EventScript_TransferredToPC
	goto {P}Done
	end

{P}Fanfare::
	playfanfare MUS_OBTAIN_ITEM
	message MossdeepCity_SpaceCenter_1F_Text_ReceivedJirachi
	waitmessage
	waitfanfare
	return

{P}Done::
	setflag FLAG_RECEIVED_JIRACHI
	release
	end

{P}Already::
	msgbox MossdeepCity_SpaceCenter_1F_Text_RocketLaunchDemandsPerfection, MSGBOX_DEFAULT
	release
	end

MossdeepCity_SpaceCenter_1F_Text_JirachiOffer:
	.string "Ah, a TRAINER who has completed the\\n"
	.string "full POKéDEX research!\\p"
	.string "We found a small, star-shaped POKéMON\\n"
	.string "asleep inside a fallen meteorite.\\p"
	.string "It only wakes for a short while.\\n"
	.string "Please take good care of it.$"

MossdeepCity_SpaceCenter_1F_Text_ReceivedJirachi:
	.string "{{PLAYER}} received JIRACHI!$"
'''
print("Scientist now offers a Lv 5 Jirachi once, when FLAG_SYS_NATIONAL_DEX is set; flag FLAG_RECEIVED_JIRACHI (0x20) added.")
if APPLY:
    open(MAP, 'w', encoding='utf-8').write(m); open(FLAGS, 'w', encoding='utf-8').write(f)
    print("APPLIED. Now run:  make -j$(nproc)")
else:
    print("DRY RUN - all required names were found; nothing written. Add --apply to write it.")
