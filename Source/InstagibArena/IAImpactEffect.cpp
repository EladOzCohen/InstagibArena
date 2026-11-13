// Instagib Arena

#include "IAImpactEffect.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AIAImpactEffect::AIAImpactEffect()
{
	PrimaryActorTick.bCanEverTick = true;
	SetReplicates(false);

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Flash = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Flash"));
	Flash->SetupAttachment(Root);
	Flash->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Flash->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereFinder.Succeeded())
	{
		Flash->SetStaticMesh(SphereFinder.Object);
	}

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Root);
	Light->SetCastShadows(false);
	Light->SetAttenuationRadius(380.f);
	Light->SetSourceRadius(12.f);
	Light->SetIntensity(0.f);
}

void AIAImpactEffect::Init(const FVector& Normal, const FLinearColor& Color, float InScale, int32 SparkCount)
{
	Scale = InScale;
	Life = 0.55f + 0.2f * FMath::Min(InScale, 2.f);

	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody"));
	UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!Base || !CubeMesh)
	{
		Destroy();
		return;
	}

	SparkMaterial = UMaterialInstanceDynamic::Create(Base, this);
	SparkMaterial->SetVectorParameterValue(TEXT("Color"), Color);
	SparkMaterial->SetScalarParameterValue(TEXT("Glow"), 9.f);
	SparkMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.4f);

	// The flash is a soft additive ball (bright in the middle, fading to its rim) instead of a hard white sphere.
	if (UMaterialInterface* Shell = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAGlowShell.M_IAGlowShell")))
	{
		FlashMaterial = UMaterialInstanceDynamic::Create(Shell, this);
		FlashMaterial->SetVectorParameterValue(TEXT("Color"), FMath::Lerp(Color, FLinearColor::White, 0.35f));
		FlashMaterial->SetScalarParameterValue(TEXT("Exponent"), 2.4f);
		FlashMaterial->SetScalarParameterValue(TEXT("HideCaps"), 0.f);
		FlashGlow = 4.5f;
	}
	else
	{
		FlashMaterial = UMaterialInstanceDynamic::Create(Base, this);
		FlashMaterial->SetVectorParameterValue(TEXT("Color"), FMath::Lerp(Color, FLinearColor::White, 0.55f));
		FlashGlow = 14.f;
	}
	FlashMaterial->SetScalarParameterValue(TEXT("Glow"), FlashGlow);
	Flash->SetMaterial(0, FlashMaterial);

	Light->SetLightColor(Color);

	const FVector Up = Normal.GetSafeNormal();
	for (int32 I = 0; I < SparkCount; ++I)
	{
		UStaticMeshComponent* Spark = NewObject<UStaticMeshComponent>(this);
		Spark->SetStaticMesh(CubeMesh);
		Spark->SetMaterial(0, SparkMaterial);
		Spark->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Spark->SetCastShadow(false);
		Spark->SetupAttachment(RootComponent);
		Spark->RegisterComponent();
		Spark->SetWorldLocation(GetActorLocation());
		Sparks.Add(Spark);

		const float Speed = FMath::FRandRange(180.f, 520.f) * (0.7f + 0.5f * Scale);
		Velocities.Add(FMath::VRandCone(Up, FMath::DegreesToRadians(65.f)) * Speed);
	}
}

void AIAImpactEffect::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	Age += DeltaSeconds;
	if (Age >= Life)
	{
		Destroy();
		return;
	}

	// Sparks: ballistic, stretched along their velocity, thinning out.
	const float Fade = 1.f - Age / Life;
	for (int32 I = 0; I < Sparks.Num(); ++I)
	{
		UStaticMeshComponent* Spark = Sparks[I];
		FVector& Velocity = Velocities[I];
		Velocity.Z -= 900.f * DeltaSeconds;
		Spark->AddWorldOffset(Velocity * DeltaSeconds);

		const float Speed = Velocity.Size();
		const float Length = FMath::Clamp(Speed * 0.03f, 3.f, 14.f) * FMath::Pow(Scale, 0.7f);
		const float Thickness = FMath::Max(0.15f, 0.9f * Fade * FMath::Pow(Scale, 0.6f));
		Spark->SetWorldRotation(Velocity.Rotation());
		Spark->SetWorldScale3D(FVector(Length, Thickness, Thickness) / 100.f);
	}

	// Flash: a sphere that swells and fades within the first fifth of a second.
	const float FlashT = FMath::Clamp(Age / 0.2f, 0.f, 1.f);
	if (FlashT < 1.f)
	{
		const float Size = (8.f + 30.f * FMath::Sqrt(FlashT)) * FMath::Pow(Scale, 0.8f);
		Flash->SetWorldScale3D(FVector(Size / 100.f));
		FlashMaterial->SetScalarParameterValue(TEXT("Glow"), FlashGlow * (1.f - FlashT));
	}
	else
	{
		Flash->SetVisibility(false);
	}

	const float LightT = FMath::Clamp(Age / 0.3f, 0.f, 1.f);
	Light->SetIntensity(32.f * FMath::Pow(Scale, 0.8f) * (1.f - LightT) * (1.f - LightT));
}
