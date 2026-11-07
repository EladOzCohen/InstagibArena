// Instagib Arena

#include "IAAudioSubsystem.h"
#include "InstagibArena.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Parse.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	const TCHAR* SoundPath(EIASound Sound, int32 Variant)
	{
		switch (Sound)
		{
		case EIASound::Footstep:
		{
			static const TCHAR* const Steps[] = {
				TEXT("/Game/Audio/SFX/S_Footstep01.S_Footstep01"), TEXT("/Game/Audio/SFX/S_Footstep02.S_Footstep02"),
				TEXT("/Game/Audio/SFX/S_Footstep03.S_Footstep03"), TEXT("/Game/Audio/SFX/S_Footstep04.S_Footstep04") };
			return Steps[Variant % UE_ARRAY_COUNT(Steps)];
		}
		case EIASound::Land:         return TEXT("/Game/Audio/SFX/S_Land.S_Land");
		case EIASound::Jump:         return TEXT("/Game/Audio/SFX/S_Jump.S_Jump");
		case EIASound::DoubleJump:   return TEXT("/Game/Audio/SFX/S_DoubleJump.S_DoubleJump");
		case EIASound::Dodge:        return TEXT("/Game/Audio/SFX/S_Dodge.S_Dodge");
		case EIASound::InstagibFire: return TEXT("/Game/Audio/SFX/S_InstagibFire.S_InstagibFire");
		case EIASound::HitConfirm:   return TEXT("/Game/Audio/SFX/S_HitConfirm.S_HitConfirm");
		case EIASound::KillConfirm:  return TEXT("/Game/Audio/SFX/S_KillConfirm.S_KillConfirm");
		case EIASound::Death:        return TEXT("/Game/Audio/SFX/S_Death.S_Death");
		case EIASound::Spawn:        return TEXT("/Game/Audio/SFX/S_Spawn.S_Spawn");
		case EIASound::UIClick:      return TEXT("/Game/Audio/SFX/S_UiClick.S_UiClick");
		case EIASound::UIStart:      return TEXT("/Game/Audio/SFX/S_UiStart.S_UiStart");
		case EIASound::MatchStart:   return TEXT("/Game/Audio/SFX/S_MatchStart.S_MatchStart");
		case EIASound::MatchEnd:     return TEXT("/Game/Audio/SFX/S_MatchEnd.S_MatchEnd");
		}
		return TEXT("");
	}
}

void UIAAudioSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Sounds fade out between roughly 4 and 40 meters.
	Attenuation = NewObject<USoundAttenuation>(this, TEXT("IAAttenuation"));
	FSoundAttenuationSettings& Settings = Attenuation->Attenuation;
	Settings.bAttenuate = true;
	Settings.bSpatialize = true;
	Settings.AttenuationShape = EAttenuationShape::Sphere;
	Settings.AttenuationShapeExtents = FVector(400.f, 0.f, 0.f);
	Settings.FalloffDistance = 3600.f;
	Settings.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;

	LoadSettings();

#if !UE_BUILD_SHIPPING
	// Test helper: -IASetMusic=0.3 changes (and saves) the music volume at start.
	float TestVolume = 0.f;
	if (FParse::Value(FCommandLine::Get(), TEXT("IASetMusic="), TestVolume))
	{
		SetMusicVolume(TestVolume);
	}
#endif
}

void UIAAudioSubsystem::LoadSettings()
{
	GConfig->GetFloat(TEXT("InstagibArena.Audio"), TEXT("MusicVolume"), MusicVolume, GGameUserSettingsIni);
	GConfig->GetFloat(TEXT("InstagibArena.Audio"), TEXT("SfxVolume"), SfxVolume, GGameUserSettingsIni);
	MusicVolume = FMath::Clamp(MusicVolume, 0.f, 1.f);
	SfxVolume = FMath::Clamp(SfxVolume, 0.f, 1.f);
	UE_LOG(LogInstagib, Log, TEXT("Audio: volumes loaded, music %.2f, effects %.2f"), MusicVolume, SfxVolume);
}

void UIAAudioSubsystem::SaveSettings() const
{
	GConfig->SetFloat(TEXT("InstagibArena.Audio"), TEXT("MusicVolume"), MusicVolume, GGameUserSettingsIni);
	GConfig->SetFloat(TEXT("InstagibArena.Audio"), TEXT("SfxVolume"), SfxVolume, GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}

void UIAAudioSubsystem::SetMusicVolume(float NewVolume)
{
	MusicVolume = FMath::Clamp(NewVolume, 0.f, 1.f);
	if (MusicComponent)
	{
		MusicComponent->AdjustVolume(0.05f, MusicVolume);
	}
	SaveSettings();
}

void UIAAudioSubsystem::SetSfxVolume(float NewVolume)
{
	SfxVolume = FMath::Clamp(NewVolume, 0.f, 1.f);
	SaveSettings();
}

UIAAudioSubsystem* UIAAudioSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
	if (!World || !World->GetGameInstance())
	{
		return nullptr;
	}
	return World->GetGameInstance()->GetSubsystem<UIAAudioSubsystem>();
}

bool UIAAudioSubsystem::CanPlay() const
{
	return !IsRunningDedicatedServer() && GEngine && GEngine->UseSound();
}

USoundBase* UIAAudioSubsystem::LoadAsset(const FString& Path)
{
	if (const TObjectPtr<USoundBase>* Found = Loaded.Find(Path))
	{
		return *Found;
	}

	USoundBase* Asset = LoadObject<USoundBase>(nullptr, *Path);
	if (!Asset)
	{
		UE_LOG(LogInstagib, Warning, TEXT("Audio: could not load %s (run Tools/import_audio.py?)"), *Path);
	}
	Loaded.Add(Path, Asset); // also remembers failures so the warning shows once
	return Asset;
}

USoundBase* UIAAudioSubsystem::LoadSound(EIASound Sound)
{
	const int32 Variant = (Sound == EIASound::Footstep) ? FMath::RandRange(0, 3) : 0;
	return LoadAsset(SoundPath(Sound, Variant));
}

void UIAAudioSubsystem::Play2D(EIASound Sound, float Volume, float Pitch)
{
	if (!CanPlay())
	{
		return;
	}
	if (USoundBase* Asset = LoadSound(Sound))
	{
		UGameplayStatics::PlaySound2D(GetWorld(), Asset, Volume * SfxVolume, Pitch);
	}
}

void UIAAudioSubsystem::PlayAt(EIASound Sound, const FVector& Location, float Volume, float PitchVariance)
{
	if (!CanPlay())
	{
		return;
	}
	if (USoundBase* Asset = LoadSound(Sound))
	{
		const float Pitch = 1.f + FMath::FRandRange(-PitchVariance, PitchVariance);
		UGameplayStatics::PlaySoundAtLocation(GetWorld(), Asset, Location, FRotator::ZeroRotator,
			Volume * SfxVolume, Pitch, 0.f, Attenuation);
	}
}

void UIAAudioSubsystem::PlayMusic(EIAMusic Track)
{
	if (!CanPlay() || !GetWorld())
	{
		return;
	}

	const TCHAR* Path = TEXT("/Game/Audio/Music/M_MenuTheme.M_MenuTheme");
	if (Track == EIAMusic::Battle)
	{
		Path = FMath::RandBool() ? TEXT("/Game/Audio/Music/M_Battle01.M_Battle01")
		                         : TEXT("/Game/Audio/Music/M_Battle02.M_Battle02");
	}

	USoundBase* Asset = LoadAsset(Path);
	if (!Asset)
	{
		return;
	}

	if (MusicComponent)
	{
		MusicComponent->Stop();
	}

	MusicComponent = UGameplayStatics::CreateSound2D(GetWorld(), Asset, 1.f, 1.f, 0.f, nullptr, false, false);
	if (MusicComponent)
	{
		MusicComponent->FadeIn(2.0f, MusicVolume);
		UE_LOG(LogInstagib, Log, TEXT("Audio: music %s"), Path);
	}
}
