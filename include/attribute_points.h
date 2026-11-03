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

#endif
