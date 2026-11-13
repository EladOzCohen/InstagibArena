// Instagib Arena

#include "IASettings.h"
#include "IAMapList.h"
#include "IACharacterRoster.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "RHI.h"
#include "Scalability.h"
#include "IPAddress.h"
#include "Misc/ConfigCacheIni.h"
#include "SocketSubsystem.h"

namespace
{
	const TCHAR* const Section = TEXT("InstagibArena.Settings");
	const TCHAR* const SetupSection = TEXT("InstagibArena.LastMatch");

	// Settings that are read every frame (UI scale, crosshair, mouse) are cached here. Every writer in this file calls
	// InvalidateCache(); on top of that a cached value is re-read at least once a second, in case the ini file was
	// reloaded by the engine (GameUserSettings::LoadSettings) behind our back.
	uint32 CacheGeneration = 1;
	void InvalidateCache() { ++CacheGeneration; }

	template <typename T>
	struct TCachedSetting
	{
		uint32 Generation = 0;
		double Time = -1000.0;
		T Value{};

		bool IsFresh() const { return Generation == CacheGeneration && FPlatformTime::Seconds() - Time < 1.0; }
		const T& Store(const T& NewValue)
		{
			Value = NewValue;
			Generation = CacheGeneration;
			Time = FPlatformTime::Seconds();
			return Value;
		}
	};

	float ReadFloat(const TCHAR* Key, float Default)
	{
		float Value = Default;
		GConfig->GetFloat(Section, Key, Value, GGameUserSettingsIni);
		return Value;
	}

	void WriteFloat(const TCHAR* Key, float Value)
	{
		InvalidateCache();
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
		InvalidateCache();
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
	float GetMouseSensitivity()
	{
		static TCachedSetting<float> Cache;
		return Cache.IsFresh() ? Cache.Value : Cache.Store(FMath::Clamp(ReadFloat(TEXT("MouseSensitivity"), 1.f), 0.1f, 3.f));
	}
	void SetMouseSensitivity(float Value) { WriteFloat(TEXT("MouseSensitivity"), FMath::Clamp(Value, 0.1f, 3.f)); }

	float GetFieldOfView()
	{
		static TCachedSetting<float> Cache;
		return Cache.IsFresh() ? Cache.Value : Cache.Store(FMath::Clamp(ReadFloat(TEXT("FieldOfView"), 90.f), 70.f, 110.f));
	}
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
		static TCachedSetting<int32> Cache;
		if (Cache.IsFresh())
		{
			return Cache.Value;
		}
		int32 Style = 0;
		GConfig->GetInt(Section, TEXT("CrosshairStyle"), Style, GGameUserSettingsIni);
		return Cache.Store(FMath::Clamp(Style, 0, CrosshairStyleCount - 1));
	}

	void SetCrosshairStyle(int32 Style)
	{
		InvalidateCache();
		GConfig->SetInt(Section, TEXT("CrosshairStyle"), FMath::Clamp(Style, 0, CrosshairStyleCount - 1), GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	int32 GetCrosshairColorIndex()
	{
		static TCachedSetting<int32> Cache;
		if (Cache.IsFresh())
		{
			return Cache.Value;
		}
		int32 Index = 0;
		GConfig->GetInt(Section, TEXT("CrosshairColor"), Index, GGameUserSettingsIni);
		return Cache.Store(FMath::Clamp(Index, 0, CrosshairColorCount - 1));
	}

	void SetCrosshairColorIndex(int32 Index)
	{
		InvalidateCache();
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

	float GetCrosshairScale()
	{
		static TCachedSetting<float> Cache;
		return Cache.IsFresh() ? Cache.Value : Cache.Store(FMath::Clamp(ReadFloat(TEXT("CrosshairScale"), 1.f), 0.5f, 2.f));
	}
	void SetCrosshairScale(float Scale) { WriteFloat(TEXT("CrosshairScale"), FMath::Clamp(Scale, 0.5f, 2.f)); }

	bool IsCameraBobEnabled()
	{
		static TCachedSetting<bool> Cache;
		if (Cache.IsFresh())
		{
			return Cache.Value;
		}
		bool bValue = true;
		GConfig->GetBool(Section, TEXT("CameraBob"), bValue, GGameUserSettingsIni);
		return Cache.Store(bValue);
	}

	void SetCameraBobEnabled(bool bEnabled)
	{
		InvalidateCache();
		GConfig->SetBool(Section, TEXT("CameraBob"), bEnabled, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	bool IsViewRollEnabled()
	{
		static TCachedSetting<bool> Cache;
		if (Cache.IsFresh())
		{
			return Cache.Value;
		}
		bool bValue = true;
		GConfig->GetBool(Section, TEXT("ViewRoll"), bValue, GGameUserSettingsIni);
		return Cache.Store(bValue);
	}

	void SetViewRollEnabled(bool bEnabled)
	{
		InvalidateCache();
		GConfig->SetBool(Section, TEXT("ViewRoll"), bEnabled, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}

	bool IsReducedMotion()
	{
		static TCachedSetting<bool> Cache;
		if (Cache.IsFresh())
		{
			return Cache.Value;
		}
		bool bValue = false;
		GConfig->GetBool(Section, TEXT("ReducedMotion"), bValue, GGameUserSettingsIni);
		return Cache.Store(bValue);
	}

	void SetReducedMotion(bool bEnabled)
	{
		InvalidateCache();
		GConfig->SetBool(Section, TEXT("ReducedMotion"), bEnabled, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
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

// ===================================================================================================
// MENUS block: video, audio, interface and first-run settings.
// ===================================================================================================

#include "HAL/IConsoleManager.h"
#include "Misc/App.h"

namespace IASettings
{
	float GetUiScale()
	{
		// Asked by Slate for every menu widget on every frame (DPIScale_Lambda), so it is cached.
		static TCachedSetting<float> Cache;
		return Cache.IsFresh() ? Cache.Value : Cache.Store(FMath::Clamp(ReadFloat(TEXT("UiScale"), 1.f), 0.8f, 1.5f));
	}
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

		// A port is whole digits only, from 1 to 65535.
		auto IsValidPort = [](const FString& PortText)
		{
			if (PortText.IsEmpty() || PortText.Len() > 5)
			{
				return false;
			}
			for (const TCHAR Char : PortText)
			{
				if (!FChar::IsDigit(Char))
				{
					return false;
				}
			}
			const int32 Port = FCString::Atoi(*PortText);
			return Port >= 1 && Port <= 65535;
		};
		const FText BadPort = INVTEXT("The port must be a whole number from 1 to 65535. Example: 192.168.1.20:7777");

		int32 ColonCount = 0;
		for (const TCHAR Char : Text)
		{
			ColonCount += (Char == TEXT(':')) ? 1 : 0;
		}

		// An IPv6 address must be in square brackets, with an optional port: [::1] or [::1]:7777.
		if (Text.StartsWith(TEXT("[")))
		{
			int32 Close = INDEX_NONE;
			if (!Text.FindChar(TEXT(']'), Close) || Close < 2)
			{
				Problem = INVTEXT("An IPv6 address needs a closing bracket. Example: [::1]:7777");
				return false;
			}
			const FString Rest = Text.Mid(Close + 1);
			if (!Rest.IsEmpty() && (!Rest.StartsWith(TEXT(":")) || !IsValidPort(Rest.Mid(1))))
			{
				Problem = BadPort;
				return false;
			}
			return true;
		}
		if (ColonCount > 1)
		{
			Problem = INVTEXT("Put an IPv6 address in square brackets, for example [::1]:7777. IPv4 addresses and host names need no brackets.");
			return false;
		}

		// "host" or "host:port".
		FString Host = Text;
		if (ColonCount == 1)
		{
			FString PortText;
			Text.Split(TEXT(":"), &Host, &PortText);
			if (!IsValidPort(PortText))
			{
				Problem = BadPort;
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

	void ApplyAntiAliasingForQuality()
	{
		if (IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AntiAliasingMethod")))
		{
			const int32 AntiAliasingLevel = Scalability::GetQualityLevels().AntiAliasingQuality;
			Variable->Set(AntiAliasingLevel <= 1 ? 2 : 4, ECVF_SetByGameSetting);   // 2 = TAA, 4 = TSR
		}
	}

	void ApplyStartupSettings()
	{
		// First start on this computer: let the engine measure the CPU and GPU once and choose the graphics quality,
		// so that weak laptops do not start at "Epic". The player can still change it in Settings > Video.
		{
			bool bAutoQualityDone = false;
			GConfig->GetBool(Section, TEXT("AutoQualityDone"), bAutoQualityDone, GGameUserSettingsIni);
			UGameUserSettings* GameSettings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
			if (!bAutoQualityDone && GameSettings && !FParse::Param(FCommandLine::Get(), TEXT("IANoAutoQuality")))
			{
				GameSettings->RunHardwareBenchmark();
				GameSettings->ApplyHardwareBenchmarkResults();
				const int32 BenchmarkLevel = Scalability::GetQualityLevels().GetMinQualityLevel();

				// The benchmark rates a laptop with a fast CPU too high (an Iris Xe laptop got Epic/High mixed) and returns a
				// mix of levels, which the video page shows as "Custom". Use ONE level for everything, and let integrated
				// graphics (which share memory with the CPU) start no higher than IntegratedStartLevel.
				const FString Adapter = GRHIAdapterName;
				const bool bNamedIntegrated = Adapter.Contains(TEXT("Iris")) || Adapter.Contains(TEXT("UHD")) || Adapter.Contains(TEXT("HD Graphics"))
					|| Adapter.Contains(TEXT("Radeon(TM) Graphics")) || Adapter.Contains(TEXT("Radeon Graphics")) || Adapter.Contains(TEXT("Vega"))
					|| (Adapter.Contains(TEXT("Radeon")) && Adapter.EndsWith(TEXT("M")));
				const bool bIntegrated = (bNamedIntegrated && !Adapter.Contains(TEXT(" RX "))) || GRHIDeviceIsIntegrated;
				const int32 IntegratedStartLevel = 1;
				const int32 Level = FMath::Clamp(bIntegrated ? FMath::Min(BenchmarkLevel, IntegratedStartLevel) : BenchmarkLevel, 0, 3);
				GameSettings->SetOverallScalabilityLevel(Level);
				GameSettings->ApplyNonResolutionSettings();
				GameSettings->SaveSettings();
				UE_LOG(LogTemp, Log, TEXT("InstagibArena: first start, graphics quality chosen automatically: benchmark %d, adapter '%s' (integrated %d), level %d"),
					BenchmarkLevel, *Adapter, bIntegrated ? 1 : 0, Level);
				GConfig->SetBool(Section, TEXT("AutoQualityDone"), true, GGameUserSettingsIni);
				GConfig->Flush(false, GGameUserSettingsIni);
			}
		}
		ApplyAntiAliasingForQuality();
		if (!IsMotionBlurEnabled())
		{
			SetMotionBlurEnabled(false);
		}
		FApp::SetUnfocusedVolumeMultiplier(GetMuteWhenUnfocused() ? 0.f : 1.f);
	}
}
