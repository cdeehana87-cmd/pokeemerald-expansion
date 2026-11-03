#ifndef GUARD_ATTRIBUTE_POINTS_H
#define GUARD_ATTRIBUTE_POINTS_H

#define ATTR_CAP_HP    9999
#define ATTR_CAP_OTHER 999

u16 AttrCap(u8 stat);                                   // stat = STAT_HP..STAT_SPDEF
u16 GetAttrPoints(struct Pokemon *mon, u8 stat);
void SetAttrPoints(struct Pokemon *mon, u8 stat, u16 value);
u16 GetUnspentPoints(struct Pokemon *mon);
void SetUnspentPoints(struct Pokemon *mon, u16 value);
bool8 SpendAttrPoint(struct Pokemon *mon, u8 stat, u16 amount);
u8 RollBattlePoints(void);                              // random 1..10
void AwardBattlePoints(struct Pokemon *mon);            // call once per participant per knockout

// PROTOTYPE ONLY: 1 = put every roll straight into one random attribute (no allocation menu yet)
#define ATTR_PROTOTYPE_AUTOSPEND 1

// Level used by the stat and damage formulas. Level no longer changes stats; only points do.
#define ATTR_REF_LEVEL 50

// Only attribute_points.c may write the EV/contest bytes; every other write is ignored.
extern bool8 gAttrWriteAllowed;

// New Pokemon start with level*level/ATTR_SEED_DIVISOR points in every attribute (enemy scaling).
#define ATTR_SEED_ENEMIES 1
#define ATTR_SEED_DIVISOR 25
void SeedAttrPoints(struct Pokemon *mon, u8 level);

#endif
