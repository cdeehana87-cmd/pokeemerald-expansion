#include "global.h"
#include "pokemon.h"
#include "random.h"
#include "attribute_points.h"

/*
 * Packs six attributes + unspent points into the 12 bytes normally used by
 * the six EVs and six contest stats (contests/Pokeblocks no longer usable).
 *
 * bit layout (little endian across the 12 bytes):
 *   HP 0-13 (14) | ATK 14-23 | DEF 24-33 | SPEED 34-43 | SPATK 44-53 | SPDEF 54-63 | UNSPENT 64-79 (16)
 * Index order matches STAT_HP, STAT_ATK, STAT_DEF, STAT_SPEED, STAT_SPATK, STAT_SPDEF.
 */
#define PACK_BYTES 12
#define UNSPENT_POS 64
#define UNSPENT_LEN 16

static const u16 sByteFields[PACK_BYTES] = {
    MON_DATA_HP_EV, MON_DATA_ATK_EV, MON_DATA_DEF_EV, MON_DATA_SPEED_EV,
    MON_DATA_SPATK_EV, MON_DATA_SPDEF_EV, MON_DATA_COOL, MON_DATA_BEAUTY,
    MON_DATA_CUTE, MON_DATA_SMART, MON_DATA_TOUGH, MON_DATA_SHEEN,
};
static const u8 sStatPos[6] = { 0, 14, 24, 34, 44, 54 };
static const u8 sStatLen[6] = { 14, 10, 10, 10, 10, 10 };

static void LoadBytes(struct Pokemon *mon, u8 *buf)
{
    u32 i;
    for (i = 0; i < PACK_BYTES; i++)
        buf[i] = GetMonData(mon, sByteFields[i], 0);
}

static void StoreBytes(struct Pokemon *mon, const u8 *buf)
{
    u32 i;
    for (i = 0; i < PACK_BYTES; i++)
        SetMonData(mon, sByteFields[i], &buf[i]);
}

static u32 ReadBits(const u8 *buf, u32 pos, u32 len)
{
    u32 i, v = 0;
    for (i = 0; i < len; i++)
        v |= (u32)((buf[(pos + i) >> 3] >> ((pos + i) & 7)) & 1) << i;
    return v;
}

static void WriteBits(u8 *buf, u32 pos, u32 len, u32 v)
{
    u32 i;
    for (i = 0; i < len; i++)
    {
        u8 mask = 1 << ((pos + i) & 7);
        if ((v >> i) & 1) buf[(pos + i) >> 3] |= mask;
        else              buf[(pos + i) >> 3] &= ~mask;
    }
}

u16 AttrCap(u8 stat)
{
    return stat == STAT_HP ? ATTR_CAP_HP : ATTR_CAP_OTHER;
}

u16 GetAttrPoints(struct Pokemon *mon, u8 stat)
{
    u8 buf[PACK_BYTES];
    u16 v;
    if (stat > STAT_SPDEF) return 0;
    LoadBytes(mon, buf);
    v = ReadBits(buf, sStatPos[stat], sStatLen[stat]);
    return v > AttrCap(stat) ? AttrCap(stat) : v;
}

void SetAttrPoints(struct Pokemon *mon, u8 stat, u16 value)
{
    u8 buf[PACK_BYTES];
    if (stat > STAT_SPDEF) return;
    if (value > AttrCap(stat)) value = AttrCap(stat);
    LoadBytes(mon, buf);
    WriteBits(buf, sStatPos[stat], sStatLen[stat], value);
    StoreBytes(mon, buf);
}

u16 GetUnspentPoints(struct Pokemon *mon)
{
    u8 buf[PACK_BYTES];
    LoadBytes(mon, buf);
    return ReadBits(buf, UNSPENT_POS, UNSPENT_LEN);
}

void SetUnspentPoints(struct Pokemon *mon, u16 value)
{
    u8 buf[PACK_BYTES];
    LoadBytes(mon, buf);
    WriteBits(buf, UNSPENT_POS, UNSPENT_LEN, value);
    StoreBytes(mon, buf);
}

bool8 SpendAttrPoint(struct Pokemon *mon, u8 stat, u16 amount)
{
    u16 unspent = GetUnspentPoints(mon);
    u16 cur = GetAttrPoints(mon, stat);
    if (stat > STAT_SPDEF || amount == 0 || amount > unspent || cur + amount > AttrCap(stat))
        return FALSE;
    SetAttrPoints(mon, stat, cur + amount);
    SetUnspentPoints(mon, unspent - amount);
    CalculateMonStats(mon);   // refresh cached stats
    return TRUE;
}

u8 RollBattlePoints(void)
{
    return 1 + (Random() % 3);
}

void AwardBattlePoints(struct Pokemon *mon)
{
    u16 roll = RollBattlePoints();
    u16 unspent = GetUnspentPoints(mon);
#if ATTR_PROTOTYPE_AUTOSPEND
    u8 stat = Random() % 6;
    u16 room = AttrCap(stat) - GetAttrPoints(mon, stat);
    u16 amount = roll < room ? roll : room;
#endif

    unspent = (unspent > 65535 - roll) ? 65535 : unspent + roll;
    SetUnspentPoints(mon, unspent);
#if ATTR_PROTOTYPE_AUTOSPEND
    if (amount != 0)
        SpendAttrPoint(mon, stat, amount);   // refreshes stats too
#else
    CalculateMonStats(mon);
#endif
}
