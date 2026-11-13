// Instagib Arena

#include "IAFlame.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AIAFlame::AIAFlame()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 1.f / 15.f;
	SetReplicates(false);

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Root);
	Light->SetRelativeLocation(FVector(0.f, 0.f, 45.f));
	Light->SetCastShadows(false);
	Light->SetMobility(EComponentMobility::Movable);
	Light->SetIntensityUnits(ELightUnits::Candelas);
	Light->SetUseInverseSquaredFalloff(true);
	Light->SetSpecularScale(0.4f);
	Light->SetSourceRadius(10.f);
	Light->SetIntensity(0.f);
}

void AIAFlame::BeginPlay()
{
	Super::BeginPlay();

	// Cosmetic only: a dedicated server does not need it.
	if (GetNetMode() == NM_DedicatedServer)
	{
		Destroy();
		return;
	}

	UMaterialInterface* FlameMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAFlame.M_IAFlame"));
	UMaterialInterface* EmberMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAEmbers.M_IAEmbers"));
	UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"));

	// Random per-flame phase so that neighbours do not burn in step (actor name as the source: stable per map).
	Seed = static_cast<float>(GetTypeHash(GetFName()) % 997) * 0.173f;

	const float S = FMath::Max(0.1f, FlameScale);
	const float FlameH = 78.f * S;
	const float FlameW = 88.f * S;
	// Core: hotter, paler than the outer colour.
	const FLinearColor Core = FMath::Lerp(FlameColor, FLinearColor(1.f, 0.62f, 0.16f), 0.7f);

	if (FlameMat && Plane)
	{
		for (int32 I = 0; I < 3; ++I)
		{
			UStaticMeshComponent* Quad = NewObject<UStaticMeshComponent>(this);
			Quad->SetStaticMesh(Plane);
			Quad->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Quad->SetCastShadow(false);
			Quad->SetupAttachment(GetRootComponent());
			// The plane lies flat; roll 90 stands it up, yaw turns the three quads 60 degrees apart.
			Quad->SetRelativeRotation(FRotator(0.f, 60.f * I, 90.f));
			Quad->SetRelativeScale3D(FVector(FlameW / 100.f, FlameH / 100.f, 1.f));
			Quad->SetRelativeLocation(FVector(0.f, 0.f, FlameH * 0.5f));
			Quad->SetCullDistance(5000.f);
			Quad->RegisterComponent();

			UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(FlameMat, this);
			Mid->SetVectorParameterValue(TEXT("EdgeColor"), FlameColor);
			Mid->SetVectorParameterValue(TEXT("CoreColor"), Core);
			Mid->SetScalarParameterValue(TEXT("Glow"), Glow);
			Mid->SetScalarParameterValue(TEXT("Seed"), Seed + 3.1f * I);
			Quad->SetMaterial(0, Mid);
			Quads.Add(Quad);
		}
	}

	if (bEmbers && EmberMat && Plane)
	{
		const float EmberH = 190.f * S;
		const float EmberW = 70.f * S;
		for (int32 I = 0; I < 2; ++I)
		{
			UStaticMeshComponent* Quad = NewObject<UStaticMeshComponent>(this);
			Quad->SetStaticMesh(Plane);
			Quad->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Quad->SetCastShadow(false);
			Quad->SetupAttachment(GetRootComponent());
			Quad->SetRelativeRotation(FRotator(0.f, 90.f * I + 30.f, 90.f));
			Quad->SetRelativeScale3D(FVector(EmberW / 100.f, EmberH / 100.f, 1.f));
			Quad->SetRelativeLocation(FVector(0.f, 0.f, 25.f * S + EmberH * 0.5f));
			Quad->SetCullDistance(2600.f);
			Quad->RegisterComponent();

			UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(EmberMat, this);
			Mid->SetVectorParameterValue(TEXT("EmberColor"), FMath::Lerp(FlameColor, FLinearColor(1.f, 0.7f, 0.25f), 0.5f));
			Mid->SetScalarParameterValue(TEXT("Seed"), Seed + 7.7f * I);
			Quad->SetMaterial(0, Mid);
			Quads.Add(Quad);
		}
	}

	Light->SetRelativeLocation(FVector(0.f, 0.f, 55.f * S));
	Light->SetLightColor(FMath::Lerp(FlameColor, FLinearColor(1.f, 0.75f, 0.4f), 0.4f));
	Light->SetAttenuationRadius(LightRadius);
	LightBase = LightCandela;
	if (LightCandela <= 0.f)
	{
		Light->SetVisibility(false);
		Light->DestroyComponent();
		Light = nullptr;
	}
	else
	{
		Light->SetIntensity(LightBase);
	}
	if (!Light)
	{
		SetActorTickEnabled(false);
	}
}

void AIAFlame::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!Light)
	{
		return;
	}
	// Three sines of unrelated speed make a flicker that never repeats visibly; a rare dip adds the gust.
	TimeAcc += DeltaSeconds;
	const float T = TimeAcc + Seed;
	float K = 0.86f + 0.07f * FMath::Sin(T * 9.3f) + 0.05f * FMath::Sin(T * 17.1f + 1.3f) + 0.04f * FMath::Sin(T * 3.1f + 2.2f);
	K -= 0.12f * FMath::Pow(FMath::Max(0.f, FMath::Sin(T * 1.7f + 0.4f * FMath::Sin(T * 0.9f))), 6.f);
	Light->SetIntensity(LightBase * K);
}
