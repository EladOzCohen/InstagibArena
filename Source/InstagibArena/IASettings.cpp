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

	int32 GetCrosshairStyle()
	{
		int32 Style = 0;
		GConfig->GetInt(Section, TEXT("CrosshairStyle"), Style, GGameUserSettingsIni);
		return FMath::Clamp(Style, 0, CrosshairStyleCount - 1);
	}

	void SetCrosshairStyle(int32 Style)
	{
		GConfig->SetInt(Section, TEXT("CrosshairStyle"), FMath::Clamp(Style, 0, CrosshairStyleCount - 1), GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	int32 GetCrosshairColorIndex()
	{
		int32 Index = 0;
		GConfig->GetInt(Section, TEXT("CrosshairColor"), Index, GGameUserSettingsIni);
		return FMath::Clamp(Index, 0, CrosshairColorCount - 1);
	}

	void SetCrosshairColorIndex(int32 Index)
	{
		GConfig->SetInt(Section, TEXT("CrosshairColor"), FMath::Clamp(Index, 0, CrosshairColorCount - 1), GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	FLinearColor GetCrosshairColor()
	{
		static const FLinearColor Palette[CrosshairColorCount] = {
			FLinearColor(1.0f, 1.0f, 1.0f), FLinearColor(0.25f, 1.0f, 0.3f), FLinearColor(0.2f, 0.9f, 1.0f),
			FLinearColor(1.0f, 0.9f, 0.2f), FLinearColor(1.0f, 0.5f, 0.1f), FLinearColor(1.0f, 0.2f, 0.2f)
		};
		return Palette[GetCrosshairColorIndex()];
	}

	float GetCrosshairScale() { return FMath::Clamp(ReadFloat(TEXT("CrosshairScale"), 1.f), 0.5f, 2.f); }
	void SetCrosshairScale(float Scale) { WriteFloat(TEXT("CrosshairScale"), FMath::Clamp(Scale, 0.5f, 2.f)); }

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

// ===================================================================================================
// MENUS block: video, audio, interface and first-run settings.
// ===================================================================================================

#include "HAL/IConsoleManager.h"
#include "Misc/App.h"

namespace IASettings
{
	float GetUiScale() { return FMath::Clamp(ReadFloat(TEXT("UiScale"), 1.f), 0.8f, 1.5f); }
	void SetUiScale(float Scale) { WriteFloat(TEXT("UiScale"), FMath::RoundToFloat(FMath::Clamp(Scale, 0.8f, 1.5f) * 10.f) / 10.f); }

	bool IsMotionBlurEnabled()
	{
		bool bEnabled = true;
		GConfig->GetBool(Section, TEXT("MotionBlur"), bEnabled, GGameUserSettingsIni);
		return bEnabled;
	}

	void SetMotionBlurEnabled(bool bEnabled)
	{
		GConfig->SetBool(Section, TEXT("MotionBlur"), bEnabled, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
		if (IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MotionBlurQuality")))
		{
			Variable->Set(bEnabled ? 4 : 0, ECVF_SetByCode);
		}
	}

	bool GetMuteWhenUnfocused()
	{
		bool bMute = true;
		GConfig->GetBool(Section, TEXT("MuteWhenUnfocused"), bMute, GGameUserSettingsIni);
		return bMute;
	}

	void SetMuteWhenUnfocused(bool bMute)
	{
		GConfig->SetBool(Section, TEXT("MuteWhenUnfocused"), bMute, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
		FApp::SetUnfocusedVolumeMultiplier(bMute ? 0.f : 1.f);
	}

	bool IsTutorialDone()
	{
		bool bDone = false;
		GConfig->GetBool(Section, TEXT("TutorialDone"), bDone, GGameUserSettingsIni);
		return bDone;
	}

	void SetTutorialDone(bool bDone)
	{
		GConfig->SetBool(Section, TEXT("TutorialDone"), bDone, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	TArray<FString> GetRecentAddresses()
	{
		TArray<FString> Result;
		ReadString(TEXT("RecentAddresses")).ParseIntoArray(Result, TEXT("|"), true);
		return Result;
	}

	void AddRecentAddress(const FString& Address)
	{
		const FString Clean = Address.TrimStartAndEnd();
		if (Clean.IsEmpty())
		{
			return;
		}
		TArray<FString> List = GetRecentAddresses();
		List.RemoveAll([&Clean](const FString& Other) { return Other.Equals(Clean, ESearchCase::IgnoreCase); });
		List.Insert(Clean, 0);
		if (List.Num() > 5)
		{
			List.SetNum(5);
		}
		WriteString(TEXT("RecentAddresses"), FString::Join(List, TEXT("|")));
	}

	bool ValidateJoinAddress(const FString& Address, FText& Problem)
	{
		const FString Text = Address.TrimStartAndEnd();
		if (Text.IsEmpty())
		{
			Problem = INVTEXT("Type the host's address first.");
			return false;
		}
		if (Text.Len() > 100 || Text.Contains(TEXT(" ")) || Text.Contains(TEXT("?")) || Text.Contains(TEXT("/")) || Text.Contains(TEXT("\\")))
		{
			Problem = INVTEXT("The address cannot contain spaces or slashes. Example: 192.168.1.20");
			return false;
		}

		// A bracketed IPv6 address, or a bare one (several colons), is accepted as it is.
		int32 ColonCount = 0;
		for (const TCHAR Char : Text)
		{
			ColonCount += (Char == TEXT(':')) ? 1 : 0;
		}
		if (Text.StartsWith(TEXT("[")) || ColonCount > 1)
		{
			return true;
		}

		// "host" or "host:port".
		FString Host = Text;
		if (ColonCount == 1)
		{
			FString PortText;
			Text.Split(TEXT(":"), &Host, &PortText);
			if (!PortText.IsNumeric() || PortText.Len() > 5 || FCString::Atoi(*PortText) < 1 || FCString::Atoi(*PortText) > 65535)
			{
				Problem = INVTEXT("The port must be a number from 1 to 65535. Example: 192.168.1.20:7777");
				return false;
			}
		}
		if (Host.IsEmpty())
		{
			Problem = INVTEXT("Type the host's address before the port.");
			return false;
		}

		bool bLooksLikeIp = true;
		for (const TCHAR Char : Host)
		{
			bLooksLikeIp &= (FChar::IsDigit(Char) || Char == TEXT('.'));
		}
		if (bLooksLikeIp)
		{
			TArray<FString> Parts;
			Host.ParseIntoArray(Parts, TEXT("."), false);
			bool bValid = Parts.Num() == 4;
			for (const FString& Part : Parts)
			{
				bValid &= !Part.IsEmpty() && Part.Len() <= 3 && FCString::Atoi(*Part) <= 255;
			}
			if (!bValid)
			{
				Problem = INVTEXT("That is not a valid IP address. It has four numbers from 0 to 255, like 192.168.1.20");
				return false;
			}
			return true;
		}

		// A host name: letters, digits, dots and dashes.
		for (const TCHAR Char : Host)
		{
			if (!(FChar::IsAlnum(Char) || Char == TEXT('.') || Char == TEXT('-') || Char == TEXT('_')))
			{
				Problem = INVTEXT("The address has a character that cannot be used. Use letters, digits, dots and dashes.");
				return false;
			}
		}
		return true;
	}

	void ApplyStartupSettings()
	{
		if (!IsMotionBlurEnabled())
		{
			SetMotionBlurEnabled(false);
		}
		FApp::SetUnfocusedVolumeMultiplier(GetMuteWhenUnfocused() ? 0.f : 1.f);
	}
}
