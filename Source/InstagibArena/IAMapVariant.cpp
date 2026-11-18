// Instagib Arena

#include "IAMapVariant.h"
#include "IARuleData.h"
#include "InstagibArena.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Containers/Ticker.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/TextureCube.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

namespace
{
	/** A time of day. Units as in Tools/maplooks.py: sun in lux, exposure in EV100 (fixed), sky brightness = on-screen value. */
	struct FPreset
	{
		float SunLux;
		float SunPitch;          // 0 = the elevation of the sun (or moon) in the panorama
		FLinearColor SunRgb;     // 8-bit style colour like maplooks (stored as sRGB)
		float SunAngle;
		const TCHAR* Cube;       // /Game/Sky/T_Sky_<Cube>
		float CubeSunAz;         // where the sun is in the panorama (maplooks.HDRI)
		float CubeSunEl;
		FLinearColor Horizon;    // relative colour of the panorama's horizon (for the fog)
		float SkyIntensity;      // sky light (the only ambient light)
		FLinearColor SkyRgb;
		FLinearColor GroundRgb;  // lower hemisphere of the sky light (linear)
		float SkyBrightness;     // dome on screen
		FLinearColor SkyTint;
		bool bSunDisc;
		float FogDensity;
		float FogMaxOpacity;
		float FogStart;
		FLinearColor FogRgb;     // A < 0: from the horizon of the panorama
		float EV;
		float Bloom;
		float Saturation;
		float Contrast;
	};

	// Calibrated against the maps that are built at dusk (Downtown, Skyline: sky light about 1.1 at EV 0.5) and at night (Neon).
	const FPreset Dusk = {
		7.f, 0.f, FLinearColor(1.0f, 0.62f, 0.36f), 0.6f,
		TEXT("dusk"), 35.59f, 12.10f, FLinearColor(1.092f, 1.216f, 1.193f),
		1.15f, FLinearColor(1.0f, 0.93f, 0.95f), FLinearColor(0.20f, 0.13f, 0.12f),
		0.5f, FLinearColor(1.0f, 0.93f, 0.97f), true,
		0.0018f, 0.55f, 300.f, FLinearColor(0.f, 0.f, 0.f, -1.f),
		0.4f, 0.22f, 1.02f, 1.08f };

	const FPreset Night = {
		1.6f, 0.f, FLinearColor(0.74f, 0.83f, 1.0f), 0.8f,
		TEXT("night_city"), 36.04f, 38.46f, FLinearColor(1.046f, 1.087f, 1.170f),
		0.42f, FLinearColor(0.80f, 0.86f, 1.0f), FLinearColor(0.08f, 0.08f, 0.11f),
		0.06f, FLinearColor(0.75f, 0.85f, 1.0f), false,
		0.0020f, 0.6f, 500.f, FLinearColor(0.035f, 0.04f, 0.065f),
		-0.9f, 0.3f, 0.78f, 1.08f };

	/** Per map corrections: exposure offset (+ = darker picture), sky light and sun factors, sun pitch override (0 = keep). */
	struct FMapTweak
	{
		const TCHAR* Map;
		int32 Variant;
		float EvOffset;
		float SkyMul;
		float SunMul;
		float SunPitch;
	};
	const FMapTweak Tweaks[] = {
		{ TEXT("Neon"),     2, 0.6f, 0.6f, 0.8f, 0.f },   // already a night map: the night variant is a deeper, bluer night
		{ TEXT("Downtown"), 1, 0.0f, 1.0f, 0.8f, -5.f },  // built at dusk: the dusk variant is the late blue hour
		{ TEXT("Skyline"),  1, 0.0f, 1.0f, 0.8f, -5.f },
	};

	/** The look of the map as it was built, remembered on the first Apply. */
	struct FBuilt
	{
		TWeakObjectPtr<UDirectionalLightComponent> Sun;
		FRotator SunRotation;
		float SunLux = 10.f;
		FColor SunColor;
		float SunAngle = 0.5f;

		TWeakObjectPtr<USkyLightComponent> Sky;
		float SkyIntensity = 1.f;
		FColor SkyColor;
		TWeakObjectPtr<UTextureCube> SkyCube;
		float SkyCubeAngle = 0.f;
		FLinearColor SkyLower;
		ESkyLightSourceType SkySource = SLS_SpecifiedCubemap;

		TWeakObjectPtr<UExponentialHeightFogComponent> Fog;
		float FogDensity = 0.f;
		FLinearColor FogColor;
		float FogMaxOpacity = 1.f;
		float FogStart = 0.f;

		TWeakObjectPtr<APostProcessVolume> Post;
		FPostProcessSettings PostSettings;

		TWeakObjectPtr<UStaticMeshComponent> Dome;
		TWeakObjectPtr<UMaterialInterface> DomeMaterial;

		int32 Applied = 0;
	};

	TMap<TWeakObjectPtr<UWorld>, FBuilt>& BuiltLooks()
	{
		static TMap<TWeakObjectPtr<UWorld>, FBuilt> Map;
		return Map;
	}

	/** maplooks colours are written straight into an 8-bit FColor (sRGB). */
	FColor Color8(const FLinearColor& C)
	{
		auto B = [](float V) { return static_cast<uint8>(FMath::Clamp(FMath::RoundToInt(V * 255.f), 0, 255)); };
		return FColor(B(C.R), B(C.G), B(C.B), 255);
	}

	bool Capture(UWorld* World, FBuilt& Out)
	{
		// The sun: the strongest directional light (the maps have one).
		for (TActorIterator<ADirectionalLight> It(World); It; ++It)
		{
			UDirectionalLightComponent* C = Cast<UDirectionalLightComponent>(It->GetLightComponent());
			if (C && (!Out.Sun.IsValid() || C->Intensity > Out.Sun->Intensity))
			{
				Out.Sun = C;
			}
		}
		if (Out.Sun.IsValid())
		{
			Out.SunRotation = Out.Sun->GetComponentRotation();
			Out.SunLux = Out.Sun->Intensity;
			Out.SunColor = Out.Sun->LightColor;
			Out.SunAngle = Out.Sun->LightSourceAngle;
		}
		for (TActorIterator<ASkyLight> It(World); It; ++It)
		{
			if (USkyLightComponent* C = It->GetLightComponent())
			{
				Out.Sky = C;
				Out.SkyIntensity = C->Intensity;
				Out.SkyColor = C->LightColor;
				Out.SkyCube = C->Cubemap;
				Out.SkyCubeAngle = C->SourceCubemapAngle;
				Out.SkyLower = C->LowerHemisphereColor;
				Out.SkySource = C->SourceType;
				break;
			}
		}
		for (TActorIterator<AExponentialHeightFog> It(World); It; ++It)
		{
			if (UExponentialHeightFogComponent* C = It->GetComponent())
			{
				Out.Fog = C;
				Out.FogDensity = C->FogDensity;
				Out.FogColor = C->FogInscatteringLuminance;
				Out.FogMaxOpacity = C->FogMaxOpacity;
				Out.FogStart = C->StartDistance;
				break;
			}
		}
		for (TActorIterator<APostProcessVolume> It(World); It; ++It)
		{
			if (It->bUnbound)
			{
				Out.Post = *It;
				Out.PostSettings = It->Settings;
				break;
			}
		}
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			UStaticMeshComponent* C = It->GetStaticMeshComponent();
			UMaterialInterface* M = C ? C->GetMaterial(0) : nullptr;
			if (M && M->GetName().StartsWith(TEXT("MI_Sky_")))
			{
				Out.Dome = C;
				Out.DomeMaterial = M;
				break;
			}
		}
		return Out.Sun.IsValid() && Out.Sky.IsValid();
	}

	void Restore(FBuilt& B)
	{
		if (UDirectionalLightComponent* Sun = B.Sun.Get())
		{
			Sun->SetWorldRotation(B.SunRotation);
			Sun->SetIntensity(B.SunLux);
			Sun->SetLightFColor(B.SunColor);
			Sun->SetLightSourceAngle(B.SunAngle);
		}
		if (USkyLightComponent* Sky = B.Sky.Get())
		{
			Sky->SourceType = B.SkySource;
			Sky->SetCubemap(B.SkyCube.Get());
			Sky->SetSourceCubemapAngle(B.SkyCubeAngle);
			Sky->SetIntensity(B.SkyIntensity);
			Sky->SetLightColor(FLinearColor(B.SkyColor));
			Sky->SetLowerHemisphereColor(B.SkyLower);
		}
		if (UExponentialHeightFogComponent* Fog = B.Fog.Get())
		{
			Fog->SetFogDensity(B.FogDensity);
			Fog->SetFogInscatteringColor(B.FogColor);
			Fog->SetFogMaxOpacity(B.FogMaxOpacity);
			Fog->SetStartDistance(B.FogStart);
		}
		if (APostProcessVolume* Post = B.Post.Get())
		{
			Post->Settings = B.PostSettings;
		}
		if (UStaticMeshComponent* Dome = B.Dome.Get())
		{
			if (B.DomeMaterial.IsValid()) { Dome->SetMaterial(0, B.DomeMaterial.Get()); }
		}
	}

	/** -IAVariantTune="ev=0.4,sun=7,...": development overrides of the preset being applied. */
	void ApplyDevTune(FPreset& P)
	{
#if !UE_BUILD_SHIPPING
		FString Text;
		if (!FParse::Value(FCommandLine::Get(), TEXT("IAVariantTune="), Text, /*bShouldStopOnSeparator*/ false))
		{
			return;
		}
		TArray<FString> Pairs;
		Text.ParseIntoArray(Pairs, TEXT(","));
		for (const FString& Pair : Pairs)
		{
			FString Key, Value;
			if (!Pair.Split(TEXT("="), &Key, &Value)) { continue; }
			const float V = FCString::Atof(*Value);
			if (Key == TEXT("ev")) { P.EV = V; }
			else if (Key == TEXT("sun")) { P.SunLux = V; }
			else if (Key == TEXT("pitch")) { P.SunPitch = V; }
			else if (Key == TEXT("sky")) { P.SkyIntensity = V; }
			else if (Key == TEXT("bright")) { P.SkyBrightness = V; }
			else if (Key == TEXT("fog")) { P.FogDensity = V; }
			else if (Key == TEXT("sat")) { P.Saturation = V; }
			else if (Key == TEXT("con")) { P.Contrast = V; }
			else if (Key == TEXT("bloom")) { P.Bloom = V; }
		}
		UE_LOG(LogInstagib, Log, TEXT("MapVariant: dev tune %s"), *Text);
#endif
	}

	void ApplyPreset(UWorld* World, FBuilt& B, int32 Variant, const FString& MapName)
	{
		FPreset P = Variant == 1 ? Dusk : Night;
		float SunPitchOverride = 0.f;
		for (const FMapTweak& T : Tweaks)
		{
			if (Variant == T.Variant && MapName.Equals(T.Map, ESearchCase::IgnoreCase))
			{
				P.EV += T.EvOffset;
				P.SkyIntensity *= T.SkyMul;
				P.SunLux *= T.SunMul;
				SunPitchOverride = T.SunPitch;
			}
		}
		if (SunPitchOverride != 0.f) { P.SunPitch = SunPitchOverride; }
		ApplyDevTune(P);

		// The light keeps the azimuth the map was built with; the panorama is turned so that its sun (or moon) is there.
		const float LightYaw = B.SunRotation.Yaw;
		const float LightPitch = P.SunPitch != 0.f ? P.SunPitch : -P.CubeSunEl;
		const float SkyYaw = FRotator::NormalizeAxis(LightYaw - 180.f - P.CubeSunAz);
		const float Scene = FMath::Pow(2.f, P.EV) * 1.2f;   // fixed exposure: on-screen value -> scene value

		if (UDirectionalLightComponent* Sun = B.Sun.Get())
		{
			Sun->SetWorldRotation(FRotator(LightPitch, LightYaw, 0.f));
			Sun->SetIntensity(P.SunLux);
			Sun->SetLightFColor(Color8(P.SunRgb));
			Sun->SetLightSourceAngle(P.SunAngle);
		}

		UTextureCube* Cube = LoadObject<UTextureCube>(nullptr, *FString::Printf(TEXT("/Game/Sky/T_Sky_%s.T_Sky_%s"), P.Cube, P.Cube));
		if (USkyLightComponent* Sky = B.Sky.Get())
		{
			if (Cube)
			{
				Sky->SourceType = SLS_SpecifiedCubemap;
				Sky->SetCubemap(Cube);
				Sky->SetSourceCubemapAngle(SkyYaw);
			}
			Sky->SetIntensity(P.SkyIntensity);
			Sky->SetLightColor(FLinearColor(Color8(P.SkyRgb)));
			Sky->SetLowerHemisphereColor(P.GroundRgb);
		}

		if (UExponentialHeightFogComponent* Fog = B.Fog.Get())
		{
			FLinearColor FogRgb = P.FogRgb;
			if (FogRgb.A < 0.f)
			{
				// Like maplooks: the horizon of the panorama, a little less saturated and darker.
				const FLinearColor& H = P.Horizon;
				const float Grey = 0.2126f * H.R + 0.7152f * H.G + 0.0722f * H.B;
				const float K = P.SkyBrightness * Scene * 0.9f;
				FogRgb = FLinearColor((Grey + 0.6f * (H.R - Grey)) * K, (Grey + 0.6f * (H.G - Grey)) * K, (Grey + 0.6f * (H.B - Grey)) * K);
			}
			FogRgb.A = 1.f;
			Fog->SetFogDensity(P.FogDensity);
			Fog->SetFogInscatteringColor(FogRgb);
			Fog->SetFogMaxOpacity(P.FogMaxOpacity);
			Fog->SetStartDistance(P.FogStart);
		}

		if (APostProcessVolume* Post = B.Post.Get())
		{
			FPostProcessSettings& S = Post->Settings;
			S.bOverride_AutoExposureMinBrightness = true;
			S.bOverride_AutoExposureMaxBrightness = true;
			S.AutoExposureMinBrightness = P.EV;
			S.AutoExposureMaxBrightness = P.EV;
			S.bOverride_BloomIntensity = true;
			S.BloomIntensity = P.Bloom;
			S.bOverride_ColorSaturation = true;
			S.ColorSaturation = FVector4(P.Saturation, P.Saturation, P.Saturation, 1.f);
			S.bOverride_ColorContrast = true;
			S.ColorContrast = FVector4(P.Contrast, P.Contrast, P.Contrast, 1.f);
		}

		if (UStaticMeshComponent* Dome = B.Dome.Get())
		{
			UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(B.DomeMaterial.Get(), Dome);
			if (Mid)
			{
				if (Cube) { Mid->SetTextureParameterValue(TEXT("Cube"), Cube); }
				Mid->SetScalarParameterValue(TEXT("Rotation"), SkyYaw);
				Mid->SetScalarParameterValue(TEXT("Brightness"), P.SkyBrightness * Scene);
				Mid->SetVectorParameterValue(TEXT("Tint"), P.SkyTint);
				const FVector Toward = -FRotator(LightPitch, LightYaw, 0.f).Vector();
				Mid->SetVectorParameterValue(TEXT("SunDir"), FLinearColor(Toward.X, Toward.Y, Toward.Z, 0.f));
				Mid->SetVectorParameterValue(TEXT("SunColor"), P.SunRgb);
				Mid->SetScalarParameterValue(TEXT("SunRadius"), 1.3f);
				Mid->SetScalarParameterValue(TEXT("SunDisc"), P.bSunDisc ? 5.f * Scene : 0.f);
				Mid->SetScalarParameterValue(TEXT("SunHalo"), P.bSunDisc ? 0.18f * Scene : 0.f);
				Mid->SetScalarParameterValue(TEXT("SunHaloExp"), 110.f);
				Dome->SetMaterial(0, Mid);
			}
		}

		UE_LOG(LogInstagib, Log, TEXT("MapVariant: %s on %s (sun %.1f lux from pitch %.0f yaw %.0f, sky light %.2f, EV %.2f, cube %s)"),
			IARules::VariantNames[Variant], *MapName, P.SunLux, LightPitch, LightYaw, P.SkyIntensity, P.EV, Cube ? P.Cube : TEXT("MISSING"));
	}

#if !UE_BUILD_SHIPPING
	/** -IAVariantShots=prefix: day, dusk and night of the same view in one run (scene only, no HUD). */
	void StartDevShots(UWorld* World)
	{
		static bool bStarted = false;
		FString Prefix;
		if (bStarted || !FParse::Value(FCommandLine::Get(), TEXT("IAVariantShots="), Prefix))
		{
			return;
		}
		bStarted = true;
		float At = 18.f;
		FParse::Value(FCommandLine::Get(), TEXT("IAVariantShotsAt="), At);
		const TWeakObjectPtr<UWorld> WeakWorld(World);
		for (int32 Step = 0; Step < IARules::VariantCount; ++Step)
		{
			// Each step: apply the variant, wait 2 s for the sky light to settle, take the picture.
			FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WeakWorld, Step](float)
			{
				if (UWorld* W = WeakWorld.Get()) { IAMapVariant::Apply(W, Step); }
				return false;
			}), At + Step * 3.f);
			FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([Prefix, Step](float)
			{
				const FString Path = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("IAShots") / FString::Printf(TEXT("%s_%s.png"), *Prefix, IARules::VariantKeys[Step]));
				FScreenshotRequest::RequestScreenshot(Path, /*bShowUI*/ false, /*bAddFilenameSuffix*/ false);
				UE_LOG(LogInstagib, Log, TEXT("MapVariant: screenshot %s"), *Path);
				return false;
			}), At + Step * 3.f + 2.f);
		}
	}
#endif
}

void IAMapVariant::Apply(UWorld* World, int32 Variant)
{
	if (!World || World->GetNetMode() == NM_DedicatedServer)
	{
		return;
	}
#if !UE_BUILD_SHIPPING
	StartDevShots(World);
#endif
	const FString MapName = IARules::MapShortName(World->GetMapName());
	Variant = FMath::Clamp(Variant, 0, IARules::VariantCount - 1);
	if (!IARules::MapHasVariants(MapName))
	{
		return;
	}

	TMap<TWeakObjectPtr<UWorld>, FBuilt>& Looks = BuiltLooks();
	for (auto It = Looks.CreateIterator(); It; ++It)
	{
		if (!It->Key.IsValid()) { It.RemoveCurrent(); }   // worlds of earlier matches
	}
	FBuilt* Built = Looks.Find(World);
	if (!Built)
	{
		if (Variant == 0)
		{
			return;   // nothing changed yet, nothing to do
		}
		FBuilt Fresh;
		if (!Capture(World, Fresh))
		{
			UE_LOG(LogInstagib, Warning, TEXT("MapVariant: %s has no sun or sky light, the time of day stays"), *MapName);
			return;
		}
		Built = &Looks.Add(World, Fresh);
	}
	if (Built->Applied == Variant)
	{
		return;
	}
	Restore(*Built);
	if (Variant != 0)
	{
		ApplyPreset(World, *Built, Variant, MapName);
	}
	Built->Applied = Variant;
}
