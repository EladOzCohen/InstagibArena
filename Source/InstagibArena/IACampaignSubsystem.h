// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IACampaignData.h"
#include "IACampaignSubsystem.generated.h"

/**
 * Progress of the campaign "The Apex League". Lives for the whole session (it survives level changes), is saved in
 * GameUserSettings.ini (section InstagibArena.Campaign) after every change, and builds the travel options of a match.
 *
 * Match numbers here are zero based (0..IACampaign::MatchCount - 1); the URL option Camp= carries number + 1, 0 = not a campaign match.
 */
UCLASS()
class INSTAGIBARENA_API UIACampaignSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** True when a campaign was started and not reset. */
	bool HasCampaign() const { return bStarted; }

	/** Starts a new campaign and forgets the old one. Difficulty: 0 relaxed (-1 skill level), 1 normal, 2 hard (+1). */
	void StartNewCampaign(const FString& InHeroName, int32 InHeroLook, int32 InDifficulty);
	void ResetCampaign();

	const FString& GetHeroName() const { return HeroName; }
	int32 GetHeroLook() const { return HeroLook; }
	int32 GetDifficulty() const { return Difficulty; }

	/** The first match that has not been won (0..MatchCount; MatchCount means the ladder is complete). */
	int32 GetNextMatch() const { return NextMatch; }
	bool IsComplete() const { return NextMatch >= IACampaign::MatchCount; }
	bool IsMatchUnlocked(int32 Index) const { return Index >= 0 && Index < IACampaign::MatchCount && Index <= NextMatch; }

	/** 0..3 stars of a match (0 = never won). */
	int32 GetStars(int32 Index) const;
	int32 GetTotalStars() const;

	/** The squad: recruited characters in the order they joined (at most IACampaign::MaxSquadMates). */
	const TArray<int32>& GetSquad() const { return Squad; }
	bool IsRecruited(int32 Look) const { return Squad.Contains(Look); }

	/** Bot skill of a match after the difficulty setting. */
	int32 GetEffectiveSkill(int32 MatchIndex) const;

	/** 0 = none chosen, 1 or 2 = the ending the player took (the index in IACampaign::Endings() + 1). */
	int32 GetEnding() const { return Ending; }
	void SetEnding(int32 Value);

	/** The URL options (without the map) of a match, e.g. "Mode=TDM?ScoreLimit=25?Bots=5?...?Camp=4". */
	FString BuildTravelOptions(int32 MatchIndex) const;

	/** The short name of the map that is really played (a stand-in while a planned map does not exist yet). */
	static FString ResolveMapName(const TCHAR* ShortName);

	/** The asset path of a map by its short name ("Foundry" -> "/Game/Maps/DM-Foundry"), after ResolveMapName. */
	static FString MapPath(const TCHAR* ShortName);

	/** Called by the game mode when a campaign match ends. Records the result, recruits, advances the ladder, saves. */
	void RecordResult(int32 MatchIndex, bool bWon, int32 Stars);

	/** The characters of one side in a match: Squad (allies, after the League's draft fills the free places) and the enemy faction. */
	TArray<int32> BuildAllyLooks(int32 MatchIndex) const;
	TArray<int32> BuildEnemyLooks(int32 MatchIndex) const;

	/** The last campaign match that ended in this session, for the ladder screen to tell. Match = -1 when nothing is waiting. */
	struct FLastResult
	{
		int32 Match = -1;
		bool bWon = false;
		int32 Stars = 0;
	};
	FLastResult LastResult;

	/** True after a campaign match: the main menu then opens on the ladder instead of the main screen. */
	bool bOpenLadderOnMenu = false;

	/** URL option value: match number + 1, 0 when the match is not a campaign match. */
	static constexpr const TCHAR* UrlOption = TEXT("Camp");

private:
	void Load();
	void Save() const;

	bool bStarted = false;
	FString HeroName;
	int32 HeroLook = 0;
	int32 Difficulty = 1;
	int32 NextMatch = 0;
	int32 Ending = 0;
	TArray<int32> StarsPerMatch;
	TArray<int32> Squad;
};
