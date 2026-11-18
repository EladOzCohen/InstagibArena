// Instagib Arena
#pragma once

#include "CoreMinimal.h"

/**
 * The data of the rewards system (docs/REWARDS_DESIGN.md): rewards, medals, ranks, titles. Pure data, no engine objects.
 * A reward is unlocked either by a counter reaching a threshold (Stat + Threshold) or by an event in the code (Stat is null).
 */
namespace IAReward
{
	struct FReward
	{
		FName Id;
		FString Category;   // "Gunsmith", "Kill effect", "Character", "Title", "Arena", "Rules", "Audio"
		FString Name;
		FString Desc;
		FString Stat;       // counter name, empty for an event reward
		int64 Threshold;
		bool bHumor;
		FString Req;        // the requirement as text
	};

	struct FMedal
	{
		const TCHAR* Name;
		const TCHAR* Stat;
		const TCHAR* What;
		int64 Tier[5];
	};

	struct FRank
	{
		const TCHAR* Name;
		int64 Points;
	};

	inline const TCHAR* const TierNames[5] = { TEXT("Rust"), TEXT("Bronze"), TEXT("Silver"), TEXT("Gold"), TEXT("Obsidian") };
	inline const int32 TierPoints[5] = { 50, 100, 150, 250, 400 };

	/** The counters: KillsCounted (weighted, see the rules), Wins, Matches, Losses, Deaths, Captures, Guards (returns + carrier kills), AirKills, LongKills,
	 *  SurvWaves, Flawless, SharpMatches, BestStreak (max), BestWave (max), MapsWon (distinct maps won), Stars, WonMap_<Map>, AP (apex points). */
	inline const TArray<FMedal>& Medals()
	{
		static const TArray<FMedal> List = {
			{ TEXT("Slayer"),       TEXT("KillsCounted"), TEXT("kills"),                       { 100, 500, 1000, 3000, 10000 } },
			{ TEXT("Sharpshooter"), TEXT("SharpMatches"), TEXT("matches with 10 kills and 40% accuracy"), { 3, 10, 30, 75, 200 } },
			{ TEXT("Champion"),     TEXT("Wins"),         TEXT("wins"),                        { 5, 25, 75, 200, 500 } },
			{ TEXT("Flagbearer"),   TEXT("Captures"),     TEXT("flag captures"),               { 5, 25, 75, 200, 500 } },
			{ TEXT("Guardian"),     TEXT("Guards"),       TEXT("flag returns and carrier kills"), { 10, 50, 150, 400, 1000 } },
			{ TEXT("Skybound"),     TEXT("AirKills"),     TEXT("kills in the air"),            { 10, 50, 150, 400, 1000 } },
			{ TEXT("Longshot"),     TEXT("LongKills"),    TEXT("kills from 40 m or more"),     { 10, 50, 150, 400, 1000 } },
			{ TEXT("Survivor"),     TEXT("SurvWaves"),    TEXT("survival waves cleared"),      { 10, 40, 100, 250, 600 } },
			{ TEXT("Untouchable"),  TEXT("Flawless"),     TEXT("matches without a death"),     { 1, 5, 15, 40, 100 } },
			{ TEXT("Streak"),       TEXT("BestStreak"),   TEXT("best kill streak"),            { 5, 8, 12, 16, 20 } },
			{ TEXT("Explorer"),     TEXT("MapsWon"),      TEXT("different arenas won"),        { 3, 6, 9, 12, 14 } },
			{ TEXT("Campaigner"),   TEXT("Stars"),        TEXT("campaign stars"),              { 10, 25, 40, 55, 60 } },
		};
		return List;
	}

	inline const TArray<FRank>& Ranks()
	{
		static const TArray<FRank> List = {
			{ TEXT("Recruit"), 0 }, { TEXT("Contender"), 500 }, { TEXT("Challenger"), 2000 }, { TEXT("Veteran"), 6000 },
			{ TEXT("Champion"), 15000 }, { TEXT("Legend"), 40000 }, { TEXT("Apex"), 100000 },
		};
		return List;
	}

	/** The arenas that have day / dusk / night variants (not the space arenas, not Quarry). */
	inline const TArray<const TCHAR*>& VariantMaps()
	{
		static const TArray<const TCHAR*> List = { TEXT("Foundry"), TEXT("Temple"), TEXT("Dock"), TEXT("Skyline"), TEXT("Neon"), TEXT("Forge"),
			TEXT("Glacier"), TEXT("Canyon"), TEXT("Citadel"), TEXT("Downtown") };
		return List;
	}

	inline const TArray<FReward>& All()
	{
		static TArray<FReward> List;
		if (List.Num() > 0)
		{
			return List;
		}
		auto Add = [](FName Id, const FString& Cat, const FString& Name, const FString& Desc, const FString& Stat, int64 Threshold, const FString& Req, bool bHumor = false)
		{
			List.Add({ Id, Cat, Name, Desc, Stat, Threshold, bHumor, Req });
		};

		// Gunsmith (kills counted)
		Add("G1", TEXT("Gunsmith"), TEXT("Beam colours"), TEXT("Six colours for your beam."), TEXT("KillsCounted"), 100, TEXT("100 kills"));
		Add("G2", TEXT("Gunsmith"), TEXT("Rifle finishes"), TEXT("Matt, polished steel, brushed brass."), TEXT("KillsCounted"), 250, TEXT("250 kills"));
		Add("G3", TEXT("Gunsmith"), TEXT("Beam styles"), TEXT("Needle, Lance and Pulse beams."), TEXT("KillsCounted"), 500, TEXT("500 kills"));
		Add("G4", TEXT("Gunsmith"), TEXT("The Gunsmith"), TEXT("Free colours for body, accent and core, and two saved designs."), TEXT("KillsCounted"), 1000, TEXT("1,000 kills"));
		Add("G5", TEXT("Gunsmith"), TEXT("Rifle parts"), TEXT("Barrels, fins and stocks."), TEXT("KillsCounted"), 2500, TEXT("2,500 kills"));
		Add("G6", TEXT("Gunsmith"), TEXT("Kill counter"), TEXT("A ring on the rifle that shows your kills."), TEXT("KillsCounted"), 5000, TEXT("5,000 kills"));
		Add("G7", TEXT("Gunsmith"), TEXT("Master Gunsmith"), TEXT("A gold-plated rifle and a golden beam."), TEXT("KillsCounted"), 10000, TEXT("10,000 kills"));
		Add("G9", TEXT("Gunsmith"), TEXT("Pennant barrel"), TEXT("A barrel with a small flag."), TEXT("Captures"), 75, TEXT("Flagbearer Silver: 75 captures"));
		Add("G10", TEXT("Gunsmith"), TEXT("Ion fins"), TEXT("Glowing fins on the rifle."), TEXT("AirKills"), 150, TEXT("Skybound Silver: 150 air kills"));
		Add("G11", TEXT("Gunsmith"), TEXT("Rifle charms"), TEXT("A tiny hat, a rubber duck, a tiny cow."), TEXT("Matches"), 100, TEXT("100 matches"), true);
		Add("G12", TEXT("Gunsmith"), TEXT("Confetti beam"), TEXT("A rainbow beam."), TEXT("Matches"), 100, TEXT("100 matches"), true);
		for (int32 C = 1; C <= 5; ++C)
		{
			static const TCHAR* const Names[5] = { TEXT("Rustborn"), TEXT("Legion"), TEXT("Syndicate"), TEXT("Void Corps"), TEXT("Hollow Court") };
			Add(FName(FString::Printf(TEXT("G8_%d"), C)), TEXT("Gunsmith"), FString::Printf(TEXT("%s rifle livery"), Names[C - 1]), TEXT("A rifle livery of the faction."), TEXT(""), 0,
				FString::Printf(TEXT("Finish chapter %d of the campaign"), C));
		}
		// Kill effects
		Add("K1", TEXT("Kill effect"), TEXT("Ash"), TEXT("Enemies crumble into ash."), TEXT("KillsCounted"), 500, TEXT("Slayer Bronze: 500 kills"));
		Add("K2", TEXT("Kill effect"), TEXT("Gold Shatter"), TEXT("Enemies burst into gold."), TEXT("KillsCounted"), 3000, TEXT("Slayer Gold: 3,000 kills"));
		Add("K3", TEXT("Kill effect"), TEXT("Frost"), TEXT("Enemies shatter into ice crystals."), TEXT("WonMap_Glacier"), 10, TEXT("Win 10 matches on Glacier"));
		Add("K4", TEXT("Kill effect"), TEXT("Glitch"), TEXT("Enemies dissolve into pixels."), TEXT("AirKills"), 400, TEXT("Skybound Gold: 400 air kills"));
		Add("K5", TEXT("Kill effect"), TEXT("Ember"), TEXT("Enemies leave glowing embers."), TEXT("LongKills"), 150, TEXT("Longshot Silver: 150 long kills"));
		Add("K6", TEXT("Kill effect"), TEXT("Poof"), TEXT("A cartoon cloud with stars."), TEXT("Losses"), 50, TEXT("Lose 50 matches"), true);
		// Characters (look indices 37..43, see IACharacterRoster.h) and variants
		Add("L37", TEXT("Character"), TEXT("Regent"), TEXT("Leader of the Obsidian Crown."), TEXT(""), 0, TEXT("Defeat the Obsidian Crown in chapter 4"));
		Add("L38", TEXT("Character"), TEXT("Sentinel"), TEXT("The heavy of the Obsidian Crown."), TEXT(""), 0, TEXT("Defeat the Obsidian Crown in chapter 4"));
		Add("L39", TEXT("Character"), TEXT("Harrier"), TEXT("The scout of the Obsidian Crown."), TEXT(""), 0, TEXT("Defeat the Obsidian Crown in chapter 4"));
		Add("L40", TEXT("Character"), TEXT("Oracle"), TEXT("The caster of the Obsidian Crown."), TEXT(""), 0, TEXT("Defeat the Obsidian Crown in chapter 4"));
		Add("L41", TEXT("Character"), TEXT("Director Voss"), TEXT("The director of the Apex League."), TEXT(""), 0, TEXT("Finish the campaign"));
		Add("L42", TEXT("Character"), TEXT("Wildcard"), TEXT("The nobody who entered through the back door."), TEXT(""), 0, TEXT("Finish the campaign on hard difficulty"));
		Add("L43", TEXT("Character"), TEXT("Gino Gasket"), TEXT("A plumber has entered the arena."), TEXT(""), 0, TEXT("Finish the campaign"), true);
		Add("C3", TEXT("Character"), TEXT("Kestrel, Champion Years"), TEXT("The mentor in his champion armour."), TEXT(""), 0, TEXT("Take the first ending"));
		Add("C4", TEXT("Character"), TEXT("Sovereign, Unbound"), TEXT("The champion without crown and helmet."), TEXT(""), 0, TEXT("Take the second ending"));
		for (int32 C = 1; C <= 5; ++C)
		{
			Add(FName(FString::Printf(TEXT("C6_%d"), C)), TEXT("Character"), FString::Printf(TEXT("Veteran livery, chapter %d"), C), TEXT("Veteran colours for the four characters of the faction."), TEXT(""), 0,
				FString::Printf(TEXT("Finish chapter %d"), C));
			Add(FName(FString::Printf(TEXT("C7_%d"), C)), TEXT("Character"), FString::Printf(TEXT("Elite livery, chapter %d"), C), TEXT("Gold trim for the four characters of the faction."), TEXT(""), 0,
				FString::Printf(TEXT("3 stars in every match of chapter %d"), C));
		}
		// Titles (T<n>: the title id is n)
		Add("T1", TEXT("Title"), TEXT("Wildcard"), TEXT("Started the campaign."), TEXT(""), 0, TEXT("Start the campaign"));
		Add("T2", TEXT("Title"), TEXT("Ferrum Survivor"), TEXT("Finished chapter 1."), TEXT(""), 0, TEXT("Finish chapter 1"));
		Add("T3", TEXT("Title"), TEXT("Aurelia Champion"), TEXT("Finished chapter 2."), TEXT(""), 0, TEXT("Finish chapter 2"));
		Add("T4", TEXT("Title"), TEXT("Meridian Ghost"), TEXT("Finished chapter 3."), TEXT(""), 0, TEXT("Finish chapter 3"));
		Add("T5", TEXT("Title"), TEXT("Cryos Veteran"), TEXT("Finished chapter 4."), TEXT(""), 0, TEXT("Finish chapter 4"));
		Add("T6", TEXT("Title"), TEXT("Nexus Conqueror"), TEXT("Finished chapter 5."), TEXT(""), 0, TEXT("Finish the campaign"));
		Add("T7", TEXT("Title"), TEXT("The Executioner"), TEXT("1,000 kills."), TEXT("KillsCounted"), 1000, TEXT("1,000 kills"));
		Add("T8", TEXT("Title"), TEXT("Flagbearer"), TEXT("100 flag captures."), TEXT("Captures"), 100, TEXT("100 captures"));
		Add("T9", TEXT("Title"), TEXT("Ghost"), TEXT("A match without a death."), TEXT("Flawless"), 1, TEXT("Win a match without dying"));
		Add("T10", TEXT("Title"), TEXT("Last Stand"), TEXT("Wave 15 in endless survival."), TEXT("BestWave"), 15, TEXT("Reach wave 15 in Endless Survival"));
		Add("T11", TEXT("Title"), TEXT("Legend of the Apex"), TEXT("Every medal in gold."), TEXT(""), 0, TEXT("All 12 medals at Gold"));
		Add("T12", TEXT("Title"), TEXT("Professional Victim"), TEXT("1,000 deaths."), TEXT("Deaths"), 1000, TEXT("Die 1,000 times"), true);
		Add("T13", TEXT("Title"), TEXT("Participation Trophy"), TEXT("25 matches in a row without a win."), TEXT("MaxLossStreak"), 25, TEXT("Lose 25 matches in a row"), true);
		// Arenas
		for (const TCHAR* Map : VariantMaps())
		{
			Add(FName(FString::Printf(TEXT("MV_%s_Dusk"), Map)), TEXT("Arena"), FString::Printf(TEXT("%s at dusk"), Map), TEXT("The same arena in the evening light."),
				FString::Printf(TEXT("WonMap_%s"), Map), 10, FString::Printf(TEXT("Win 10 matches on %s"), Map));
			Add(FName(FString::Printf(TEXT("MV_%s_Night"), Map)), TEXT("Arena"), FString::Printf(TEXT("%s at night"), Map), TEXT("The same arena in the dark."),
				FString::Printf(TEXT("WonMap_%s"), Map), 30, FString::Printf(TEXT("Win 30 matches on %s"), Map));
		}
		Add("M2", TEXT("Arena"), TEXT("Apex Core"), TEXT("The control room of Director Voss, a secret duel arena."), TEXT(""), 0, TEXT("Finish the campaign on hard difficulty"));
		Add("M4", TEXT("Arena"), TEXT("The Pasture"), TEXT("A very small farm. Do not ask."), TEXT(""), 0, TEXT("A secret"), true);
		// Rules
		Add("R1", TEXT("Rules"), TEXT("Low Gravity"), TEXT("Long, high jumps."), TEXT("AirKills"), 25, TEXT("25 air kills"));
		Add("R2", TEXT("Rules"), TEXT("Slow Finish"), TEXT("The last kill of the match in slow motion."), TEXT("Wins"), 25, TEXT("25 wins"));
		Add("R3", TEXT("Rules"), TEXT("Hardcore"), TEXT("No HUD, only the game."), TEXT("Wins"), 50, TEXT("50 wins"));
		Add("R4", TEXT("Rules"), TEXT("Endless Survival"), TEXT("Survival without an end, with a personal best."), TEXT("BestWave"), 10, TEXT("Reach wave 10 in Survival"));
		Add("R5", TEXT("Rules"), TEXT("Apex+ (Heat)"), TEXT("Five heat levels for the campaign."), TEXT(""), 0, TEXT("Finish the campaign"));
		Add("R6", TEXT("Rules"), TEXT("Big Heads"), TEXT("Huge heads. Just for laughs."), TEXT("Matches"), 50, TEXT("50 matches"), true);
		// Audio
		Add("A1", TEXT("Audio"), TEXT("Jukebox"), TEXT("Listen to the music of the game in the menu."), TEXT("AP"), 500, TEXT("Reach rank Contender"));
		for (int32 C = 1; C <= 5; ++C)
		{
			Add(FName(FString::Printf(TEXT("A2_%d"), C)), TEXT("Audio"), FString::Printf(TEXT("Menu view, chapter %d"), C), TEXT("A new background for the main menu."), TEXT(""), 0,
				FString::Printf(TEXT("Finish chapter %d"), C));
		}
		Add("A3", TEXT("Audio"), TEXT("Photo Mode"), TEXT("A free camera in the pause menu."), TEXT(""), 0, TEXT("Finish the campaign"));
		Add("A4", TEXT("Audio"), TEXT("Funny kill messages"), TEXT("Kill feed messages with a wink."), TEXT("Matches"), 50, TEXT("50 matches"), true);
		return List;
	}

	inline const FReward* Find(FName Id)
	{
		for (const FReward& R : All())
		{
			if (R.Id == Id) { return &R; }
		}
		return nullptr;
	}

	/** The unlock id of a character look (37 and up are unlockable). */
	inline FName LookId(int32 Look) { return FName(FString::Printf(TEXT("L%d"), Look)); }
}
