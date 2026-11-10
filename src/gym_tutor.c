#include "global.h"
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
