Common_EventScript_PkmnCenterNurse::
	lock
	faceplayer
	goto AttrPoints_EventScript_Offer

Common_EventScript_PkmnCenterNurse_Main::
	setvar VAR_0x8004, 0
.if !IS_FRLG
	specialvar VAR_RESULT, CountPlayerTrainerStars
	goto_if_eq VAR_RESULT, 4, EventScript_PkmnCenterNurse_GoldCard
.endif
	msgbox gText_WouldYouLikeToRestYourPkmn, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, EventScript_PkmnCenterNurse_HealPkmn
	goto_if_eq VAR_RESULT, NO, EventScript_PkmnCenterNurse_Goodbye
	end

EventScript_PkmnCenterNurse_Goodbye::
	message gText_WeHopeToSeeYouAgain
	return

@ VAR_0x8004 is 1 when player has Gold Card; jumps are identical
EventScript_PkmnCenterNurse_HealPkmn::
	incrementgamestat GAME_STAT_USED_POKECENTER
	call_if_eq VAR_0x8004, 0, EventScript_PkmnCenterNurse_IllTakeYourPkmn
	call_if_eq VAR_0x8004, 1, EventScript_PkmnCenterNurse_IllTakeYourPkmn2
	waitmessage
	call EventScript_PkmnCenterNurse_TakeAndHealPkmn
	goto_if_unset FLAG_POKERUS_EXPLAINED, EventScript_PkmnCenterNurse_CheckPokerus
	goto EventScript_PkmnCenterNurse_CheckTrainerHillAndUnionRoom
	end

EventScript_PkmnCenterNurse_IllTakeYourPkmn::
	message gText_IllTakeYourPkmn
	return

EventScript_PkmnCenterNurse_IllTakeYourPkmn2::
	message gText_IllTakeYourPkmn2
	return

EventScript_PkmnCenterNurse_TakeAndHealPkmn::
	hidefollower 0
	applymovement VAR_0x800B, Movement_PkmnCenterNurse_Turn
	waitmovement 0
	dofieldeffect FLDEFF_POKECENTER_HEAL
.if OW_UNION_DISABLE_CHECK == FALSE && OW_FLAG_MOVE_UNION_ROOM_CHECK != 0
	setflag OW_FLAG_MOVE_UNION_ROOM_CHECK
	call CableClub_OnResume
	clearflag OW_FLAG_MOVE_UNION_ROOM_CHECK
.endif
	waitfieldeffect FLDEFF_POKECENTER_HEAL
	applymovement VAR_0x800B, Common_Movement_WalkInPlaceFasterDown
	waitmovement 0
	special HealPlayerParty
	callnative UpdateFollowingPokemon
	return

EventScript_PkmnCenterNurse_CheckTrainerHillAndUnionRoom::
	specialvar VAR_RESULT, PlayerNotAtTrainerHillEntrance
	goto_if_eq VAR_RESULT, 0, EventScript_PkmnCenterNurse_ReturnPkmn
	specialvar VAR_RESULT, BufferUnionRoomPlayerName
	copyvar VAR_0x8008, VAR_RESULT
	goto_if_eq VAR_0x8008, 0, EventScript_PkmnCenterNurse_ReturnPkmn
	goto_if_eq VAR_0x8008, 1, EventScript_PkmnCenterNurse_PlayerWaitingInUnionRoom
	end

@ VAR_0x8004 is 1 when player has Gold Card
EventScript_PkmnCenterNurse_ReturnPkmn::
	goto_if_eq VAR_0x8004, 1, EventScript_PkmnCenterNurse_ReturnPkmn2
	message gText_RestoredPkmnToFullHealth
	waitmessage
	applymovement VAR_0x800B, Movement_PkmnCenterNurse_Bow
	waitmovement 0
	message gText_WeHopeToSeeYouAgain
	return

EventScript_PkmnCenterNurse_ReturnPkmn2::
	message gText_ThankYouForWaiting
	waitmessage
	applymovement VAR_0x800B, Movement_PkmnCenterNurse_Bow
	waitmovement 0
	message gText_WeHopeToSeeYouAgain2
	return

EventScript_PkmnCenterNurse_PlayerWaitingInUnionRoom::
	goto_if_set FLAG_NURSE_UNION_ROOM_REMINDER, EventScript_PkmnCenterNurse_ReturnPkmn
	msgbox gText_RestoredPkmnToFullHealth, MSGBOX_DEFAULT
	setflag FLAG_NURSE_UNION_ROOM_REMINDER
	message CableClub_Text_PlayerIsWaiting
	waitmessage
	applymovement VAR_0x800B, Movement_PkmnCenterNurse_Bow
	waitmovement 0
	message gText_WeHopeToSeeYouAgain
	return

EventScript_PkmnCenterNurse_CheckPokerus::
	specialvar VAR_RESULT, IsPokerusInParty
	goto_if_eq VAR_RESULT, TRUE, EventScript_PkmnCenterNurse_ExplainPokerus
	goto_if_eq VAR_RESULT, FALSE, EventScript_PkmnCenterNurse_CheckTrainerHillAndUnionRoom
	end

EventScript_PkmnCenterNurse_ExplainPokerus::
	message gText_PokerusExplanation
	setflag FLAG_POKERUS_EXPLAINED
	return

EventScript_PkmnCenterNurse_GoldCard::
	goto_if_set FLAG_NURSE_MENTIONS_GOLD_CARD, EventScript_PkmnCenterNurse_AskForUsual
	setflag FLAG_NURSE_MENTIONS_GOLD_CARD
	msgbox gText_WelcomeCutShort, MSGBOX_DEFAULT
	playse SE_PIN
	applymovement VAR_0x800B, Common_Movement_ExclamationMark
	waitmovement 0
	applymovement VAR_0x800B, Common_Movement_Delay48
	waitmovement 0
	msgbox gText_NoticesGoldCard, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, EventScript_PkmnCenterNurse_GoldCardHealPkmn
	message gText_WeHopeToSeeYouAgain2
	return

EventScript_PkmnCenterNurse_AskForUsual::
	msgbox gText_YouWantTheUsual, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, EventScript_PkmnCenterNurse_GoldCardHealPkmn
	message gText_WeHopeToSeeYouAgain2
	return

EventScript_PkmnCenterNurse_GoldCardHealPkmn::
	setvar VAR_0x8004, 1
	goto EventScript_PkmnCenterNurse_HealPkmn
	end

Movement_PkmnCenterNurse_Bow:
	nurse_joy_bow
	delay_4
	step_end

Movement_PkmnCenterNurse_Turn:
	walk_in_place_faster_left
	step_end

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
	.string "Would you like to spend attribute\n"
	.string "points earned in battle?$"

AttrPoints_Text_WhichMon:
	.string "Which party member should receive\n"
	.string "the points?$"

AttrPoints_Text_HasPoints:
	.string "{STR_VAR_1} has {STR_VAR_2} unspent\n"
	.string "points. Which attribute should rise?$"

AttrPoints_Text_HowMany:
	.string "How many points?$"

AttrPoints_Text_Spent:
	.string "{STR_VAR_1}'s {STR_VAR_2} rose by\n"
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
