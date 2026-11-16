// Instagib Arena
//
// Data of the campaign "The Apex League": factions, the story cast and the 20 matches in 5 chapters.
// Pure data: no logic. The story is told by the texts here (briefings, win and lose lines) and by the announcer.
// Character indices (look = IACharacters::GetLook index) beyond IACharacters::LookCount are planned new characters; until
// they exist the roster wraps them onto an existing look (see IACharacters::GetLook), so the tables stay valid.

#pragma once

#include "CoreMinimal.h"

enum class EIACampaignMode : uint8
{
	Duel,            // 1 against 1, first to the limit
	FreeForAll,
	TeamDeathmatch,
	CaptureTheFlag,
	Survival         // waves of bots against the player and the squad
};

/** A faction: the opponents of one chapter. Looks lists the characters that belong to it. */
struct FIACampaignFaction
{
	const TCHAR* Name;
	const TCHAR* Tagline;
	const TCHAR* Lore;
	FLinearColor Color;
	TArray<int32> Looks;
};

/** What the third star asks for. The values refer to the human player (Margin and EnemyScore to the match score). */
enum class EIABonus : uint8
{
	MaxDeaths,       // at most Value deaths
	MinAccuracy,     // accuracy of at least Value percent
	MinStreak,       // a kill streak of at least Value
	MinKills,        // at least Value kills
	MinCaptures,     // at least Value flag captures of your own
	MaxEnemyScore,   // the enemy side scored at most Value (captures or frags of the best opponent)
	MinMargin        // won by at least Value points of the match score
};

struct FIABonusGoal
{
	EIABonus Kind;
	int32 Value;

	FString ToText() const
	{
		switch (Kind)
		{
		case EIABonus::MaxDeaths:     return Value <= 0 ? TEXT("Win without dying.") : FString::Printf(TEXT("Win with %d or fewer deaths."), Value);
		case EIABonus::MinAccuracy:   return FString::Printf(TEXT("Win with an accuracy of %d percent or more."), Value);
		case EIABonus::MinStreak:     return FString::Printf(TEXT("Get a kill streak of %d or more."), Value);
		case EIABonus::MinKills:      return FString::Printf(TEXT("Win with at least %d kills of your own."), Value);
		case EIABonus::MinCaptures:   return Value <= 1 ? FString(TEXT("Win and capture a flag yourself.")) : FString::Printf(TEXT("Win and capture %d flags yourself."), Value);
		case EIABonus::MaxEnemyScore: return Value <= 0 ? FString(TEXT("Win without letting the enemy score.")) : FString::Printf(TEXT("Win and let the enemy score at most %d."), Value);
		case EIABonus::MinMargin:     return FString::Printf(TEXT("Win by %d or more points."), Value);
		}
		return FString();
	}
};

/** One match of the ladder. */
struct FIACampaignMatch
{
	int32 Chapter;                 // 0..4
	const TCHAR* Title;
	const TCHAR* Map;              // short name as in IAMaps ("Foundry"), the game maps it to the asset path
	EIACampaignMode Mode;
	int32 BotSkill;                // 0 rookie ... 6 master
	int32 EnemyCount;
	int32 AllyCount;               // squad mates that fight with you (filled from the recruited squad, then by the League's draft)
	int32 Limit;                   // frags, captures, or waves in survival
	int32 TimeLimitMinutes;
	int32 Faction;                 // index in IACampaign::Factions
	int32 RecruitLook;             // character who joins your squad after you win (-1: none)
	const TCHAR* Briefing;
	const TCHAR* WinLine;
	const TCHAR* LoseLine;
	FIABonusGoal Bonus;            // the third star: a small extra goal, checked by the game mode
};

/** Story characters who do not fight in the ladder as ordinary opponents. */
struct FIACampaignCast
{
	const TCHAR* Name;
	const TCHAR* Role;
	const TCHAR* Bio;
	int32 Look;
};

namespace IACampaign
{
	inline constexpr int32 ChapterCount = 5;
	inline constexpr int32 MatchCount = 20;
	inline constexpr int32 MaxSquadMates = 3;

	// Look indices of planned new characters (they wrap onto existing looks until they are modelled).
	inline constexpr int32 LookKestrel = 15;
	inline constexpr int32 LookSovereign = 16;

	struct FChapter
	{
		const TCHAR* Name;
		const TCHAR* Planet;
		const TCHAR* Intro;     // text before the first match of the chapter
		const TCHAR* Outro;     // text after the last
	};

	inline const TArray<FChapter>& Chapters()
	{
		static const TArray<FChapter> Items = {
			{ TEXT("WILDCARD"), TEXT("FERRUM"),
			  TEXT("Ferrum is a dead industrial moon. The Apex League keeps its qualifiers here, in abandoned foundries, run by the Rustborn: scrap-built fighters who hate the League and love a fight. You have no team, no sponsor, and no name that anyone remembers. You have one entry slot, and a stranger in the stands who is watching you."),
			  TEXT("The Rustborn bow out. Somebody in the Apex League has noticed the Wildcard. A message arrives: you are through to the Frontier.") },
			{ TEXT("THE FRONTIER LEAGUE"), TEXT("AURELIA"),
			  TEXT("Aurelia was an empire once. Its ruins are now arenas, and its soldiers, the Aurelian Legion, fight as they marched: in formation, without mercy. This is where the League stops being a game. Teams, discipline, and a rival team in black glass who have started to follow you."),
			  TEXT("You face Obsidian Crown in front of a billion people. Win or lose, the League has made up its mind about you. The Director smiles. Kestrel does not. Now the real climb begins.") },
			{ TEXT("THE GRAND LEAGUE"), TEXT("MERIDIAN"),
			  TEXT("Meridian is the capital: a planet that is one city, built up for ten thousand years. The Neon Syndicate runs its arenas and its bets. Everything here is for sale, including the result. The League says it is clean. The scoreboard says otherwise."),
			  TEXT("The Syndicate falls. The flags that stuck, the pads that went dark: it was never luck. Someone is steering the arenas. You still do not know who.") },
			{ TEXT("THE CHAMPIONSHIP"), TEXT("CRYOS AND THE ORBIT"),
			  TEXT("Past the last planet is the ring: cold worlds, drifting stations, wrecks of ships that never came home. The Void Corps, soldiers raised in vacuum, hold the Championship. Orbit is quiet. Nobody can hear you fall."),
			  TEXT("Obsidian Crown is broken. Voss has not hidden it: the arenas obey him. And the champion, Sovereign, has asked to speak to you.") },
			{ TEXT("NEXUS"), TEXT("NEXUS"),
			  TEXT("Nexus is the oldest arena in the League, built on a dead star's remains. Its guards are the Hollow Court, masked in the faces of old gods, the last fighters before the throne. Beyond them is Sovereign, who has not lost in eleven seasons."),
			  TEXT("You stand at the end of it all. Whatever you choose, nothing in the League will be the same.") },
		};
		return Items;
	}

	inline const TArray<FIACampaignFaction>& Factions()
	{
		static const TArray<FIACampaignFaction> Items = {
			// 0 Ferrum
			{ TEXT("Rustborn"), TEXT("We were here first."),
			  TEXT("Anarchists of Ferrum. They build their armour from the moon's own scrap and answer to nobody. Fast, loud, careless with their own lives."),
			  FLinearColor(0.85f, 0.35f, 0.08f), { 17, 18, 19, 20, 9, 7, 4 } },
			// 1 Aurelia
			{ TEXT("Aurelian Legion"), TEXT("Hold the line."),
			  TEXT("The army of a fallen empire, still drilling in its own ruins. Matching armour, matching tactics, one voice on the radio."),
			  FLinearColor(0.78f, 0.62f, 0.16f), { 21, 22, 23, 24, 10, 5, 0, 2 } },
			// 2 Meridian
			{ TEXT("Neon Syndicate"), TEXT("Everything has a price."),
			  TEXT("Corporate fighters of the capital: bright, sleek, ruthless with the clock. They win by getting there first and leaving with the prize."),
			  FLinearColor(0.15f, 0.8f, 0.95f), { 25, 26, 27, 28, 1, 8, 13 } },
			// 3 Cryos and the orbit
			{ TEXT("Void Corps"), TEXT("Silence is a weapon."),
			  TEXT("Soldiers raised in vacuum. Slow to anger, perfect in aim. They never waste a shot and never leave a position."),
			  FLinearColor(0.6f, 0.75f, 0.9f), { 29, 30, 31, 32, 11, 3, 12 } },
			// 4 Nexus
			{ TEXT("Hollow Court"), TEXT("We are what remains."),
			  TEXT("The last guards of Nexus, masked as the old gods of the arena. Nobody has seen their faces. Nobody has beaten them twice."),
			  FLinearColor(0.75f, 0.1f, 0.1f), { 33, 34, 35, 36, 14, 6 } },
		};
		return Items;
	}

	inline const TArray<FIACampaignCast>& Cast()
	{
		static const TArray<FIACampaignCast> Items = {
			{ TEXT("Kestrel"), TEXT("Your mentor"),
			  TEXT("A veteran who left the League and never said why. He watches your first match from the stands and finds you afterwards. He teaches without explaining."),
			  LookKestrel },
			{ TEXT("Director Voss"), TEXT("Head of the Apex League"),
			  TEXT("A voice on the screens. He built the League out of a dozen failing arenas and sells it to a hundred worlds. He is charming, patient, and always in control."),
			  -1 },
			{ TEXT("Sovereign"), TEXT("The Champion"),
			  TEXT("Eleven seasons undefeated. Sovereign has not smiled in any of them. Under contract to the League, and tired."),
			  LookSovereign },
			{ TEXT("Obsidian Crown"), TEXT("The League's house team"),
			  TEXT("The best of every faction in black glass armour. They are always on the broadcast. They are never in the loser's column."),
			  -1 },
		};
		return Items;
	}

	/** The 20 matches in order. Index = match number - 1. */
	inline const TArray<FIACampaignMatch>& Matches()
	{
		static const TArray<FIACampaignMatch> Items = {
			// ---- Chapter 1: Ferrum (Rustborn) ----
			{ 0, TEXT("First Blood"), TEXT("Foundry"), EIACampaignMode::Duel, 0, 1, 0, 10, 8, 0, -1,
			  TEXT("A qualifier on an empty foundry floor. One opponent, one rifle. A man in the stands, wrapped in a grey coat, is watching."),
			  TEXT("Clean. The man in the grey coat nods once and is gone before you can find him."),
			  TEXT("You go down hard. The man in the grey coat stays in his seat. Try again."),
			  { EIABonus::MaxDeaths, 3 } },
			{ 0, TEXT("The Dockside Brawl"), TEXT("Dock"), EIACampaignMode::FreeForAll, 0, 3, 0, 15, 8, 0, -1,
			  TEXT("Everyone against everyone among the shipping containers. The Rustborn do not fight fair, and do not care."),
			  TEXT("You come out of the stacks on your feet. The Rustborn ask your name. You give it."),
			  TEXT("The Rustborn laugh and send you back to the start of the line."),
			  { EIABonus::MinAccuracy, 30 } },
			{ 0, TEXT("Forge Run"), TEXT("Forge"), EIACampaignMode::FreeForAll, 1, 4, 0, 15, 10, 0, -1,
			  TEXT("The lava forge. Jump pads, gantries and the glare of the pit. A stranger walks the gantry above, unarmed, taking notes."),
			  TEXT("The stranger introduces himself: Kestrel. He tells you that you shoot well and move badly. He is right."),
			  TEXT("The forge is not forgiving. Kestrel says nothing. That is worse."),
			  { EIABonus::MaxDeaths, 4 } },
			{ 0, TEXT("Gearhead's Challenge"), TEXT("Foundry"), EIACampaignMode::TeamDeathmatch, 1, 3, 2, 20, 10, 0, 9,
			  TEXT("Gearhead, the best mechanic on Ferrum, wants to see if you are worth building a team around. Two League draftees fight beside you."),
			  TEXT("Gearhead wipes the grease off his goggles and holds out a wrench. He will keep your rifle clean. Gearhead joins your squad."),
			  TEXT("Gearhead shakes his head. Not yet."),
			  { EIABonus::MinKills, 8 } },

			// ---- Chapter 2: Aurelia (Aurelian Legion) ----
			{ 1, TEXT("Ruins of the Empire"), TEXT("Temple"), EIACampaignMode::TeamDeathmatch, 2, 3, 2, 25, 10, 1, -1,
			  TEXT("The Legion forms up in the old temple. Their formation is perfect until someone breaks it. Find the weak flank."),
			  TEXT("A Legion officer salutes you, which has never happened to anyone from Ferrum."),
			  TEXT("The Legion closes ranks and does not stop. Regroup."),
			  { EIABonus::MaxDeaths, 3 } },
			{ 1, TEXT("Last Stand on the Mesa"), TEXT("Canyon"), EIACampaignMode::Survival, 2, 4, 2, 5, 12, 1, 10,
			  TEXT("A Legion drill: hold the mesa against wave after wave of recruits. Aurelia, a legionary who trained under the empire's last general, is on the mesa with you."),
			  TEXT("Five waves down. Aurelia lowers her sword. She has seen enough: she will fight beside you. Aurelia joins your squad."),
			  TEXT("The mesa falls. The Legion marches on."),
			  { EIABonus::MaxDeaths, 2 } },
			{ 1, TEXT("The First Flag"), TEXT("Citadel"), EIACampaignMode::CaptureTheFlag, 2, 4, 3, 3, 12, 1, -1,
			  TEXT("The Citadel: two keeps, a river, a village. Take their flag back to your keep. Defend yours. The Legion has done this for a thousand years."),
			  TEXT("Three captures. Kestrel, watching from the wall, says only: that was good."),
			  TEXT("The Legion keeps its flag. You keep your lessons."),
			  { EIABonus::MaxEnemyScore, 0 } },
			{ 1, TEXT("Black Glass"), TEXT("Skyline"), EIACampaignMode::TeamDeathmatch, 3, 4, 3, 25, 12, 1, -1,
			  TEXT("The Frontier final: rooftops at sunset. Across the bridge waits Obsidian Crown, the League's house team in black glass armour. This is the first time you meet them."),
			  TEXT("You beat the Crown, and the League throws the result out an hour later: an irregularity in the scoring. Kestrel says: they cheat when you win. Remember that."),
			  TEXT("Obsidian Crown wins by nine. The broadcast runs it as a highlight. Kestrel says: you are not ready yet."),
			  { EIABonus::MinStreak, 3 } },

			// ---- Chapter 3: Meridian (Neon Syndicate) ----
			{ 2, TEXT("Night Shift"), TEXT("Neon"), EIACampaignMode::Duel, 3, 1, 0, 10, 8, 2, -1,
			  TEXT("Meridian by night. A Syndicate duellist, Vesper, bets on herself in every match and has not lost a credit in two years."),
			  TEXT("Vesper reads the scoreboard and for once the number is not hers. She flips you a chip and says: I will see you in the district."),
			  TEXT("Vesper collects. She is polite about it."),
			  { EIABonus::MaxDeaths, 1 } },
			{ 2, TEXT("Hostile Takeover"), TEXT("Downtown"), EIACampaignMode::CaptureTheFlag, 3, 4, 3, 3, 12, 2, 1,
			  TEXT("The Syndicate's home district. Flags, rooftops, a plaza with a fountain. They will trade anything, including your position."),
			  TEXT("Vesper has changed sides. She had been waiting for someone worth betting on. Vesper joins your squad."),
			  TEXT("The Syndicate takes the district and the credit."),
			  { EIABonus::MinCaptures, 2 } },
			{ 2, TEXT("Rooftop Rules"), TEXT("Skyline"), EIACampaignMode::Survival, 4, 5, 3, 6, 12, 2, -1,
			  TEXT("A Syndicate betting game: survive six waves on the rooftops. Somewhere the odds are being displayed to a billion people."),
			  TEXT("They paid out on you. Several people will not forgive that."),
			  TEXT("The odds were always against you."),
			  { EIABonus::MaxDeaths, 2 } },
			{ 2, TEXT("The Fix"), TEXT("Downtown"), EIACampaignMode::TeamDeathmatch, 4, 4, 3, 30, 12, 2, -1,
			  TEXT("The Syndicate's last stand. In the third minute the flags jam and the jump pads go dark: Voss is steering the arena. Your squad has seen it too."),
			  TEXT("The Syndicate folds. In the confusion you read a message in the arena system: the League is not fair. You knew that. Now you can prove it."),
			  TEXT("The Syndicate wins. Nobody asks why the arena went dark."),
			  { EIABonus::MaxDeaths, 3 } },

			// ---- Chapter 4: Cryos and the orbit (Void Corps) ----
			{ 3, TEXT("Frozen Outpost"), TEXT("Glacier"), EIACampaignMode::CaptureTheFlag, 4, 4, 3, 3, 12, 3, -1,
			  TEXT("Cryos: ice and a radio tower. The Void Corps fight like they were born in silence: one shot, one kill, no wasted words."),
			  TEXT("The Corps' commander salutes. Tundra, their scout, asks to be remembered."),
			  TEXT("The Corps does not gloat. It does not need to."),
			  { EIABonus::MaxDeaths, 3 } },
			{ 3, TEXT("The Ring"), TEXT("Orbital"), EIACampaignMode::FreeForAll, 5, 5, 0, 20, 12, 3, -1,
			  TEXT("A station on the edge of a gas giant. Windows the size of buildings. Nobody here fires without a reason."),
			  TEXT("Six hundred kilometres below, the planet turns. You are still standing."),
			  TEXT("The station keeps its silence."),
			  { EIABonus::MinAccuracy, 45 } },
			{ 3, TEXT("Sealed Quarry"), TEXT("Quarry"), EIACampaignMode::CaptureTheFlag, 5, 4, 3, 3, 15, 3, -1,
			  TEXT("A mining pit under a dome. Mid-match the flags stick to their bases and will not move. Voss makes no effort to hide it. You push through anyway."),
			  TEXT("You win without the flags. Voss goes quiet on the channel. The audience does not."),
			  TEXT("Voss lets the flag stay stuck, and the Corps takes the pit."),
			  { EIABonus::MinCaptures, 1 } },
			{ 3, TEXT("Derelict"), TEXT("Derelict"), EIACampaignMode::TeamDeathmatch, 5, 4, 3, 30, 15, 3, -1,
			  TEXT("A dead ship, drifting. Obsidian Crown waits in the dark. This time you have a squad, a reason, and a plan."),
			  TEXT("Obsidian Crown falls. Their captain looks into the camera and says only: Sovereign wants to see you."),
			  TEXT("The Crown wins again, and this time they are not gentle."),
			  { EIABonus::MinMargin, 10 } },

			// ---- Chapter 5: Nexus (Hollow Court) ----
			{ 4, TEXT("Before the Throne"), TEXT("Orbital"), EIACampaignMode::Survival, 5, 5, 3, 8, 15, 4, -1,
			  TEXT("The last survival trial before Nexus. Eight waves. The Hollow Court sends its masked guards one by one."),
			  TEXT("Eight waves cleared. A door opens at the end of the station that was not there before."),
			  TEXT("Eight waves was too many. The door does not open."),
			  { EIABonus::MaxDeaths, 2 } },
			{ 4, TEXT("The Court"), TEXT("Quarry"), EIACampaignMode::FreeForAll, 6, 6, 0, 30, 15, 4, -1,
			  TEXT("Nexus, the arena of arenas. The Hollow Court wears the faces of old gods. They are the last fighters before the throne, and they do not die easily."),
			  TEXT("The masks fall one by one. Nobody had seen their faces. They are only people. That, somehow, is worse."),
			  TEXT("The gods do not get up. You do not rise."),
			  { EIABonus::MinStreak, 5 } },
			{ 4, TEXT("Throne Room"), TEXT("Citadel"), EIACampaignMode::CaptureTheFlag, 6, 4, 3, 5, 20, 4, -1,
			  TEXT("The semi-final: two sides of the oldest keep in the League. The Court plays like a single mind. Voss watches from every screen."),
			  TEXT("Five captures. Voss is no longer smiling on the broadcast. Kestrel stands up from the stands."),
			  TEXT("The Court holds the keep. Sovereign is told to wait."),
			  { EIABonus::MaxEnemyScore, 0 } },
			{ 4, TEXT("Sovereign"), TEXT("Downtown"), EIACampaignMode::Duel, 6, 1, 0, 15, 12, 4, -1,
			  TEXT("The final. One against one, with every world watching. Sovereign has not lost in eleven seasons, and has been waiting for someone to try."),
			  TEXT("Sovereign lowers the rifle. They say: finally. The Apex League has a new champion. The question is what you do with the crown."),
			  TEXT("Sovereign does not gloat. They say: come back when you are ready. Voss says nothing at all."),
			  { EIABonus::MinAccuracy, 50 } },
		};
		return Items;
	}

	/** The two endings (shown after match 20). The player chooses. */
	struct FEnding
	{
		const TCHAR* Title;
		const TCHAR* ChoiceLabel;
		const TCHAR* Text;
	};

	inline const TArray<FEnding>& Endings()
	{
		static const TArray<FEnding> Items = {
			{ TEXT("THE CHAMPION"), TEXT("Take the crown"),
			  TEXT("You take the crown. Voss offers you the same contract he gave Sovereign, and you sign. The League has a new face. The arenas keep running, and nobody asks who steers them. Sovereign leaves on the next ship, free. You will not see them again.") },
			{ TEXT("THE LAST MATCH"), TEXT("Expose the League"),
			  TEXT("You do not take the crown. You send the arena logs, every flag that stuck and every pad that went dark, to a hundred worlds at once. The League falls, and Voss with it. The arenas are free. The fighters keep fighting, but now it is only a game.") },
		};
		return Items;
	}
}
