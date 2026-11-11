// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IAAudioSubsystem.generated.h"

class USoundBase;
class USoundAttenuation;
class UAudioComponent;

UENUM(BlueprintType)
enum class EIASound : uint8
{
	Footstep,
	Land,
	Jump,
	DoubleJump,
	Dodge,
	InstagibFire,
	HitConfirm,
	KillConfirm,
	Death,
	Spawn,
	UIClick,
	UIStart,
	MatchStart,
	MatchEnd,

	// ---- match HUD cues (Tools/gen_audio.py hud_cues)
	CountdownTick,
	CountdownGo,
	ClockTick,
	Warning,
	FirstBlood,
	MedalLow,
	MedalMid,
	MedalHigh,
	StreakLow,
	StreakMid,
	StreakHigh,
	LeadGain,
	LeadLose,
	LeadTie,
	Victory,
	Defeat
};

UENUM(BlueprintType)
enum class EIAMusic : uint8
{
	Menu,
	Battle
};

/**
 * Plays every sound of the game. Assets are loaded by path the first time
 * they are needed (see /Game/Audio, made by Tools/gen_audio.py), so a missing
 * file only logs a warning instead of breaking the game.
 */
UCLASS()
class INSTAGIBARENA_API UIAAudioSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Finds the subsystem from any object that lives in a world. May return null. */
	static UIAAudioSubsystem* Get(const UObject* WorldContext);

	/** Flat sound for the local player (menu clicks, hit feedback, own weapon). */
	void Play2D(EIASound Sound, float Volume = 1.f, float Pitch = 1.f);

	/** 3D sound that fades with distance. PitchVariance of 0.08 means +/- 8 percent. */
	void PlayAt(EIASound Sound, const FVector& Location, float Volume = 1.f, float PitchVariance = 0.f);

	/** Starts the music for the current world, replacing whatever played before. */
	void PlayMusic(EIAMusic Track);

	/** Volumes from 0 to 1. They are remembered between sessions. */
	float GetMusicVolume() const { return MusicVolume; }
	float GetSfxVolume() const { return SfxVolume; }
	void SetMusicVolume(float NewVolume);
	void SetSfxVolume(float NewVolume);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float MusicVolume = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Audio")
	float SfxVolume = 1.0f;

private:
	void LoadSettings();
	void SaveSettings() const;
	USoundBase* LoadSound(EIASound Sound);
	USoundBase* LoadAsset(const FString& Path);
	bool CanPlay() const;

	UPROPERTY(Transient)
	TMap<FString, TObjectPtr<USoundBase>> Loaded;

	UPROPERTY(Transient)
	TObjectPtr<USoundAttenuation> Attenuation;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> MusicComponent;
};
