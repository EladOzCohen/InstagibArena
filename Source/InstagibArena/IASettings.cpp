// Instagib Arena

#include "IASettings.h"
#include "IAMapList.h"
#include "IACharacterRoster.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "IPAddress.h"
#include "Misc/ConfigCacheIni.h"
#include "SocketSubsystem.h"

namespace
{
	const TCHAR* const Section = TEXT("InstagibArena.Settings");
	const TCHAR* const SetupSection = TEXT("InstagibArena.LastMatch");

	float ReadFloat(const TCHAR* Key, float Default)
	{
		float Value = Default;
		GConfig->GetFloat(Section, Key, Value, GGameUserSettingsIni);
		return Value;
	}

	void WriteFloat(const TCHAR* Key, float Value)
	{
		GConfig->SetFloat(Section, Key, Value, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	FString ReadString(const TCHAR* Key)
	{
		FString Value;
		GConfig->GetString(Section, Key, Value, GGameUserSettingsIni);
		return Value;
	}

	void WriteString(const TCHAR* Key, const FString& Value)
	{
		GConfig->SetString(Section, Key, *Value, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}
}

// ---------------------------------------------------------------- last match

void FIAMatchSetup::Load()
{
	bool bTeam = bTeamGame;
	GConfig->GetBool(SetupSection, TEXT("TeamGame"), bTeam, GGameUserSettingsIni);
	GConfig->GetInt(SetupSection, TEXT("Map"), MapIndex, GGameUserSettingsIni);
	GConfig->GetInt(SetupSection, TEXT("Character"), CharacterIndex, GGameUserSettingsIni);
	GConfig->GetInt(SetupSection, TEXT("Bots"), BotCount, GGameUserSettingsIni);
	GConfig->GetInt(SetupSection, TEXT("BotSkill"), BotSkill, GGameUserSettingsIni);
	GConfig->GetInt(SetupSection, TEXT("ScoreLimit"), ScoreLimit, GGameUserSettingsIni);
	GConfig->GetInt(SetupSection, TEXT("TimeLimit"), TimeLimit, GGameUserSettingsIni);

	// A file edited by hand, or written by another version, must not break the menu.
	bTeamGame = bTeam;
	MapIndex = FMath::Clamp(MapIndex, 0, IAMaps::Count - 1);
	CharacterIndex = FMath::Clamp(CharacterIndex, 0, IACharacters::LookCount - 1);
	BotCount = (BotCount <= 0) ? 0 : FMath::Clamp(BotCount, 2, 10);
	BotSkill = FMath::Clamp(BotSkill, 0, 2);
	ScoreLimit = FMath::Clamp(ScoreLimit, 0, 100);
	TimeLimit = FMath::Clamp(TimeLimit, 0, 30);
}

void FIAMatchSetup::Save() const
{
	GConfig->SetBool(SetupSection, TEXT("TeamGame"), bTeamGame, GGameUserSettingsIni);
	GConfig->SetInt(SetupSection, TEXT("Map"), MapIndex, GGameUserSettingsIni);
	GConfig->SetInt(SetupSection, TEXT("Character"), CharacterIndex, GGameUserSettingsIni);
	GConfig->SetInt(SetupSection, TEXT("Bots"), BotCount, GGameUserSettingsIni);
	GConfig->SetInt(SetupSection, TEXT("BotSkill"), BotSkill, GGameUserSettingsIni);
	GConfig->SetInt(SetupSection, TEXT("ScoreLimit"), ScoreLimit, GGameUserSettingsIni);
	GConfig->SetInt(SetupSection, TEXT("TimeLimit"), TimeLimit, GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}

// ---------------------------------------------------------------- settings

namespace IASettings
{
	float GetMouseSensitivity() { return FMath::Clamp(ReadFloat(TEXT("MouseSensitivity"), 1.f), 0.1f, 3.f); }
	void SetMouseSensitivity(float Value) { WriteFloat(TEXT("MouseSensitivity"), FMath::Clamp(Value, 0.1f, 3.f)); }

	float GetFieldOfView() { return FMath::Clamp(ReadFloat(TEXT("FieldOfView"), 90.f), 70.f, 110.f); }
	void SetFieldOfView(float Value) { WriteFloat(TEXT("FieldOfView"), FMath::Clamp(Value, 70.f, 110.f)); }

	FString GetPlayerName() { return ReadString(TEXT("PlayerName")); }
	void SetPlayerName(const FString& Name) { WriteString(TEXT("PlayerName"), Name.Left(16)); }

	FString GetUrlSafePlayerName()
	{
		FString Safe;
		for (const TCHAR Char : GetPlayerName())
		{
			if (FChar::IsAlnum(Char) || Char == TEXT('_') || Char == TEXT('-'))
			{
				Safe.AppendChar(Char);
			}
		}
		return Safe.Left(16);
	}

	FString GetJoinAddress()
	{
		FString Address = ReadString(TEXT("JoinAddress"));
		return Address.IsEmpty() ? TEXT("127.0.0.1") : Address;
	}

	void SetJoinAddress(const FString& Address) { WriteString(TEXT("JoinAddress"), Address.TrimStartAndEnd()); }

	FString GetLocalAddressText()
	{
		if (ISocketSubsystem* Sockets = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM))
		{
			bool bCanBindAll = false;
			const TSharedRef<FInternetAddr> Address = Sockets->GetLocalHostAddr(*GLog, bCanBindAll);
			if (Address->IsValid())
			{
				return Address->ToString(false);
			}
		}
		return FString();
	}

	bool IsFullscreen()
	{
		const UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
		return Settings && Settings->GetFullscreenMode() != EWindowMode::Windowed;
	}

	void ApplyDisplayMode(bool bFullscreen)
	{
		UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
		if (!Settings)
		{
			return;
		}

		const FIntPoint Desktop = Settings->GetDesktopResolution();
		if (bFullscreen)
		{
			Settings->SetFullscreenMode(EWindowMode::WindowedFullscreen);
			Settings->SetScreenResolution(Desktop);
		}
		else
		{
			Settings->SetFullscreenMode(EWindowMode::Windowed);
			Settings->SetScreenResolution(Desktop.X >= 1920 ? FIntPoint(1600, 900) : FIntPoint(1280, 720));
		}
		Settings->ApplySettings(false);
	}
}
