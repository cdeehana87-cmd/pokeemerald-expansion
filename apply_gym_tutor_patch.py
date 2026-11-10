# Run from the repo root:  python3 apply_gym_tutor_patch.py
# Adds the gym move post machinery and the Rustboro (Rock) post. Reuses the Move Relearner screen in its "tutor" state.
import re, os, sys
def die(m): print("STOP:", m); sys.exit(1)
MR, SPEC = 'src/move_relearner.c', 'data/specials.inc'
GYM = 'data/maps/RustboroCity_Gym/scripts.inc'
for p in (MR, SPEC, GYM):
    if not os.path.exists(p): die(f"{p} not found - run from the repo root")
if os.path.exists('src/gym_tutor.c'): die("already applied (src/gym_tutor.c exists)")
files = {p: open(p, encoding='utf-8').read() for p in (MR, SPEC, GYM)}
def edit(p, name, pattern, repl):
    new, n = re.subn(pattern, repl, files[p])
    if n != 1: die(f"'{name}' matched {n} places in {p} (expected 1) - nothing was changed")
    files[p] = new; print("ok:", name)

# ---- move_relearner.c: gym list when a gym post is active; tutor state counts as "active" during a gym post
edit(MR, 'include', r'(#include "global\.h"\n)', lambda m: m.group(1) + '#include "gym_tutor.h"\n')
edit(MR, 'gym list in the tutor move list', r'(static u32 GetRelearnerTutorMoves\(struct BoxPokemon \*mon, u16 \*moves\)\s*\{)',
     lambda m: m.group(1) + '\n    if (gGymTutorId != 0)\n        return GymTutor_GetMoves(mon, moves);\n')
edit(MR, 'tutor state active during a gym post', r'return \(FlagGet\(P_FLAG_TUTOR_MOVES\) \|\| P_ENABLE_MOVE_RELEARNERS\);',
     lambda m: 'return (gGymTutorId != 0 || FlagGet(P_FLAG_TUTOR_MOVES) || P_ENABLE_MOVE_RELEARNERS);')

# ---- specials
files[SPEC] = files[SPEC].rstrip('\n') + '\n  def_special GymTutor_Begin\n  def_special GymTutor_End\n'
print("ok: specials registered")

# ---- Rustboro gym guide: offer the post after the leader is beaten
P = 'RustboroCity_Gym_EventScript_RockTutor'
edit(GYM, 'Rustboro guide offers the Rock post',
     r'(RustboroCity_Gym_EventScript_GymGuidePostVictory::[ \t]*\n[ \t]*msgbox RustboroCity_Gym_Text_GymGuidePostVictory, MSGBOX_DEFAULT[ \t]*\n)([ \t]*)release',
     lambda m: m.group(1) + m.group(2) + 'goto ' + P + 'Offer')
files[GYM] = files[GYM].rstrip('\n') + f'''

{P}Offer::
	msgbox {P}_Text_Offer, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, {P}End
	setvar VAR_0x8004, 1
	special GymTutor_Begin
	goto {P}ChooseMon

{P}ChooseMon::
	msgbox {P}_Text_WhichMon, MSGBOX_DEFAULT
	special ChooseMonForMoveRelearner
	goto_if_ge VAR_0x8004, PARTY_SIZE, {P}End
	special IsSelectedMonEgg
	goto_if_eq VAR_RESULT, TRUE, {P}CantEgg
	goto_if_eq VAR_0x8005, 0, {P}NoMoves
	goto {P}ChooseMove

{P}ChooseMove::
	msgbox {P}_Text_WhichMove, MSGBOX_DEFAULT
	special TeachMoveRelearnerMove
	goto_if_eq VAR_0x8004, 0, {P}ChooseMon
	goto {P}End

{P}NoMoves::
	msgbox {P}_Text_NoMoves, MSGBOX_DEFAULT
	goto {P}ChooseMon

{P}CantEgg::
	msgbox {P}_Text_CantEgg, MSGBOX_DEFAULT
	goto {P}ChooseMon

{P}End::
	special GymTutor_End
	release
	end

{P}_Text_Offer:
	.string "I can teach ROCK-type moves to your\\n"
	.string "POKéMON now that you beat ROXANNE.\\p"
	.string "A POKéMON must be strong enough and\\n"
	.string "able to learn the move. Interested?$"

{P}_Text_WhichMon:
	.string "Which POKéMON should I teach?$"

{P}_Text_WhichMove:
	.string "Which move should I teach?$"

{P}_Text_NoMoves:
	.string "That POKéMON has no ROCK move it can\\n"
	.string "learn right now.$"

{P}_Text_CantEgg:
	.string "An EGG can't learn any moves.$"
'''
print("ok: Rustboro post script and text appended")

# ---- new C files
os.makedirs('include', exist_ok=True)
open('include/gym_tutor.h', 'w', encoding='utf-8').write('''#ifndef GUARD_GYM_TUTOR_H
#define GUARD_GYM_TUTOR_H

extern u8 gGymTutorId;   // 0 = no gym post active, 1..8 = which gym
u32 GymTutor_GetMoves(struct BoxPokemon *mon, u16 *moves);
void GymTutor_Begin(void);
void GymTutor_End(void);

#endif // GUARD_GYM_TUTOR_H
''')
open('src/gym_tutor.c', 'w', encoding='utf-8').write('''#include "global.h"
#include "pokemon.h"
#include "event_data.h"
#include "move_relearner.h"
#include "constants/moves.h"
#include "gym_tutor.h"

// Gym move posts. A move is offered only if: the post's gym matches, the Pokemon's level >= minLevel,
// the Pokemon does not know it yet, and it is in the Pokemon's TM/tutor list or its level-up list.
struct GymMove
{
    u8 gym;        // 1 Rustboro (Rock) ... 8 Sootopolis (Water)
    u16 move;
    u8 minLevel;
};

static const struct GymMove sGymMoves[] =
{
    // 1: Rustboro, Rock
    { 1, MOVE_ROCK_THROW,    10 },
    { 1, MOVE_ROCK_TOMB,     15 },
    { 1, MOVE_ROCK_BLAST,    20 },
    { 1, MOVE_ANCIENT_POWER, 25 },
    { 1, MOVE_ROCK_SLIDE,    30 },
    { 1, MOVE_POWER_GEM,     35 },
    { 1, MOVE_STONE_EDGE,    45 },
};

EWRAM_DATA u8 gGymTutorId = 0;

static bool32 KnowsMove(struct BoxPokemon *mon, u16 move)
{
    u32 i;
    for (i = 0; i < MAX_MON_MOVES; i++)
        if (GetBoxMonData(mon, MON_DATA_MOVE1 + i) == move)
            return TRUE;
    return FALSE;
}

static bool32 InLevelUpList(enum Species species, u16 move)
{
    u16 moves[MAX_LEVEL_UP_MOVES];
    u32 i, n = GetLevelUpMovesBySpecies(species, moves);
    for (i = 0; i < n; i++)
        if (moves[i] == move)
            return TRUE;
    return FALSE;
}

u32 GymTutor_GetMoves(struct BoxPokemon *mon, u16 *moves)
{
    enum Species species = GetBoxMonData(mon, MON_DATA_SPECIES);
    u32 level = GetBoxMonData(mon, MON_DATA_LEVEL);
    u32 i, n = 0;

    for (i = 0; i < ARRAY_COUNT(sGymMoves); i++)
    {
        const struct GymMove *g = &sGymMoves[i];
        if (g->gym != gGymTutorId || level < g->minLevel || KnowsMove(mon, g->move))
            continue;
        if (!CanLearnTeachableMove(species, g->move) && !InLevelUpList(species, g->move))
            continue;
        moves[n++] = g->move;
    }
    return n;
}

void GymTutor_Begin(void)
{
    gGymTutorId = gSpecialVar_0x8004;
    gMoveRelearnerState = MOVE_RELEARNER_TUTOR_MOVES;
}

void GymTutor_End(void)
{
    gGymTutorId = 0;
    gMoveRelearnerState = MOVE_RELEARNER_LEVEL_UP_MOVES;
}
''')
print("ok: src/gym_tutor.c and include/gym_tutor.h written")
for p, t in files.items(): open(p, 'w', encoding='utf-8').write(t)
print("DONE. Now run:  make -j$(nproc)")
