#ifndef GUARD_GYM_TUTOR_H
#define GUARD_GYM_TUTOR_H

extern u8 gGymTutorId;   // 0 = no gym post active, 1..8 = which gym
u32 GymTutor_GetMoves(struct BoxPokemon *mon, u16 *moves);
void GymTutor_Begin(void);
void GymTutor_End(void);

#endif // GUARD_GYM_TUTOR_H
