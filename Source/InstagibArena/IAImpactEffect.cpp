// Instagib Arena

#include "IAImpactEffect.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
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

	if (KillStyle > 0)
	{
		TickKill(DeltaSeconds);
		return;
	}

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

// ---------------------------------------------------------------- kill effects

float AIAImpactEffect::GetKillVanishTime(uint8 Style)
{
	switch (Style)
	{
	case 1: return 1.3f;    // Ash: the body darkens, then crumbles
	case 2: return 0.1f;    // Gold Shatter: at once
	case 3: return 0.85f;   // Frost: frozen for a moment, then shatters
	case 4: return 0.65f;   // Glitch: flickers, then dissolves
	case 6: return 0.06f;   // Poof
	default: return 3.6f;   // Ember and the standard death keep the body
	}
}

UMaterialInstanceDynamic* AIAImpactEffect::LitMaterial(const FLinearColor& Color, float Roughness, float Metallic, float Glow)
{
	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IACharacter.M_IACharacter"));
	if (!Base)
	{
		return GlowMaterial(Color, FMath::Max(Glow, 0.5f));
	}
	UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Base, this);
	M->SetVectorParameterValue(TEXT("Color"), Color);
	M->SetScalarParameterValue(TEXT("Roughness"), Roughness);
	M->SetScalarParameterValue(TEXT("Metallic"), Metallic);
	M->SetScalarParameterValue(TEXT("Glow"), Glow);
	M->SetScalarParameterValue(TEXT("Detail"), 0.f);
	KillMaterials.Add(M);
	return M;
}

UMaterialInstanceDynamic* AIAImpactEffect::GlowMaterial(const FLinearColor& Color, float Glow)
{
	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/M_IABody.M_IABody"));
	if (!Base)
	{
		return nullptr;
	}
	UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Base, this);
	M->SetVectorParameterValue(TEXT("Color"), Color);
	M->SetScalarParameterValue(TEXT("Glow"), Glow);
	M->SetScalarParameterValue(TEXT("Roughness"), 0.4f);
	KillMaterials.Add(M);
	return M;
}

AIAImpactEffect::FBit& AIAImpactEffect::AddBit(UStaticMesh* Shape, UMaterialInterface* Material, int32 Kind, float Birth, float BitLife, const FVector& Size)
{
	UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this);
	Comp->SetStaticMesh(Shape);
	Comp->SetMaterial(0, Material);
	Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Comp->SetCastShadow(false);
	Comp->SetupAttachment(RootComponent);
	Comp->SetUsingAbsoluteLocation(true);
	Comp->SetUsingAbsoluteRotation(true);
	Comp->SetUsingAbsoluteScale(true);
	Comp->SetVisibility(false);
	Comp->RegisterComponent();

	FBit& Bit = Bits.AddDefaulted_GetRef();
	Bit.Comp = Sparks.Add(Comp);
	Bit.Kind = Kind;
	Bit.Birth = Birth;
	Bit.Life = BitLife;
	Bit.Size = Size;
	Bit.Phase = FMath::FRand();
	Bit.Rot = FRotator(FMath::FRandRange(0.f, 360.f), FMath::FRandRange(0.f, 360.f), FMath::FRandRange(0.f, 360.f));
	Life = FMath::Max(Life, Birth + BitLife + 0.05f);
	return Bit;
}

FVector AIAImpactEffect::RandomBodyPoint() const
{
	const USkeletalMeshComponent* Skel = Body.Get();
	if (Skel && BodyBones.Num() > 0)
	{
		return Skel->GetBoneLocation(BodyBones[FMath::RandRange(0, BodyBones.Num() - 1)]) + FMath::VRand() * FMath::FRandRange(0.f, 7.f);
	}
	return GetActorLocation() + FVector(FMath::FRandRange(-25.f, 25.f), FMath::FRandRange(-25.f, 25.f), FMath::FRandRange(-70.f, 70.f));
}

void AIAImpactEffect::InitKill(uint8 Style, const FLinearColor& VictimColor, USkeletalMeshComponent* InBody)
{
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	UStaticMesh* Cone = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));
	if (!Cube || !Sphere || !Cone || Style == 0)
	{
		Destroy();
		return;
	}
	KillStyle = Style;
	Scale = 2.f;
	Life = 0.5f;
	Body = InBody;
	if (InBody && InBody->GetSkeletalMeshAsset())
	{
		for (int32 I = 0; I < InBody->GetNumBones(); ++I)
		{
			const FName Name = InBody->GetBoneName(I);
			const FString Text = Name.ToString();
			if (Text.StartsWith(TEXT("ik_")) || Text.StartsWith(TEXT("VB ")) || Text == TEXT("root") || Text.Contains(TEXT("_metacarpal")))
			{
				continue;
			}
			BodyBones.Add(Name);
		}
	}

	// The floor under the body, for debris that bounces.
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(IAKillFloor), false, this);
	if (InBody && InBody->GetOwner())
	{
		Params.AddIgnoredActor(InBody->GetOwner());
	}
	const FVector Down = GetActorLocation();
	FloorZ = GetWorld() && GetWorld()->LineTraceSingleByChannel(Hit, Down + FVector(0.f, 0.f, 60.f), Down - FVector(0.f, 0.f, 400.f), ECC_Visibility, Params)
		? Hit.ImpactPoint.Z + 1.5f : Down.Z - 95.f;

	FLinearColor FlashColor = FLinearColor::White;
	FLinearColor LightColor = FLinearColor::White;
	FlashGlow = 4.f;
	auto R = [](float A, float B) { return FMath::FRandRange(A, B); };

	switch (Style)
	{
	case 1: // Ash: dark flakes and a few embers leave the body, then it crumbles into a cloud of ash that settles.
	{
		FollowUntil = 1.3f;
		FlashDelay = 1.3f;
		FlashColor = FLinearColor(0.5f, 0.45f, 0.4f);
		FlashGlow = 0.9f;
		LightColor = FLinearColor(1.f, 0.35f, 0.08f);
		LightPeak = 6.f;
		LightLength = 1.6f;
		UMaterialInterface* Ash[3] = { LitMaterial(FLinearColor(0.03f, 0.03f, 0.03f), 1.f, 0.f), LitMaterial(FLinearColor(0.09f, 0.085f, 0.08f), 1.f, 0.f), LitMaterial(FLinearColor(0.2f, 0.19f, 0.18f), 1.f, 0.f) };
		UMaterialInterface* Ember = GlowMaterial(FLinearColor(1.f, 0.3f, 0.04f), 7.f);
		for (int32 I = 0; I < 20; ++I)
		{
			FBit& B = AddBit(Cube, Ash[I % 3], 0, R(0.f, 1.2f), R(1.2f, 1.8f), FVector(R(1.5f, 3.f), R(1.5f, 3.f), 0.35f));
			B.Vel = FVector(R(-25.f, 25.f), R(-25.f, 25.f), R(30.f, 90.f));
			B.Gravity = -15.f; B.Drag = 0.6f;
			B.Spin = FRotator(R(-200.f, 200.f), R(-200.f, 200.f), R(-200.f, 200.f));
		}
		for (int32 I = 0; I < 10; ++I)
		{
			FBit& B = AddBit(Cube, Ember, 0, R(0.f, 1.2f), R(0.6f, 1.2f), FVector(0.8f));
			B.Vel = FVector(R(-20.f, 20.f), R(-20.f, 20.f), R(60.f, 140.f));
			B.Gravity = -40.f; B.Drag = 0.5f;
		}
		for (int32 I = 0; I < 46; ++I)
		{
			FBit& B = AddBit(I % 4 == 0 ? Sphere : Cube, Ash[I % 3], 0, R(1.3f, 1.42f), R(1.3f, 2.2f), FVector(R(2.f, 4.5f), R(2.f, 4.5f), R(0.5f, 2.f)));
			B.Vel = FMath::VRand() * R(20.f, 70.f) + FVector(0.f, 0.f, 20.f);
			B.Gravity = 160.f; B.Drag = 1.6f; B.bBounce = true;
			B.Spin = FRotator(R(-150.f, 150.f), R(-150.f, 150.f), 0.f);
		}
		break;
	}
	case 2: // Gold Shatter: the body bursts into spinning gold shards that bounce on the floor.
	{
		FollowUntil = 0.1f;
		FlashColor = FLinearColor(1.f, 0.75f, 0.3f);
		FlashGlow = 6.f;
		LightColor = FLinearColor(1.f, 0.7f, 0.25f);
		LightPeak = 60.f;
		LightLength = 0.45f;
		UMaterialInterface* Gold[2] = { LitMaterial(FLinearColor(1.f, 0.68f, 0.24f), 0.18f, 1.f, 0.25f), LitMaterial(FLinearColor(0.85f, 0.52f, 0.14f), 0.3f, 1.f, 0.15f) };
		UMaterialInterface* Spark = GlowMaterial(FLinearColor(1.f, 0.8f, 0.35f), 8.f);
		for (int32 I = 0; I < 48; ++I)
		{
			FBit& B = AddBit(Cube, Gold[I % 2], 0, R(0.05f, 0.12f), R(1.6f, 2.4f), FVector(R(3.f, 7.f), R(1.5f, 3.5f), R(0.4f, 0.9f)));
			B.Vel = FMath::VRandCone(FVector::UpVector, FMath::DegreesToRadians(80.f)) * R(260.f, 640.f);
			B.Gravity = 980.f; B.bBounce = true;
			B.Spin = FRotator(R(-900.f, 900.f), R(-900.f, 900.f), R(-900.f, 900.f));
		}
		for (int32 I = 0; I < 20; ++I)
		{
			FBit& B = AddBit(Cube, Spark, 0, 0.05f, R(0.3f, 0.6f), FVector(6.f, 0.6f, 0.6f));
			B.Vel = FMath::VRand() * R(400.f, 800.f);
			B.Gravity = 600.f;
		}
		break;
	}
	case 3: // Frost: ice spikes grow out of the body, a cold mist, then everything shatters into ice.
	{
		FollowUntil = 0.f;
		FlashDelay = 0.85f;
		FlashColor = FLinearColor(0.6f, 0.9f, 1.f);
		FlashGlow = 3.f;
		LightColor = FLinearColor(0.5f, 0.85f, 1.f);
		LightPeak = 30.f;
		LightLength = 1.2f;
		UMaterialInterface* Ice[2] = { LitMaterial(FLinearColor(0.55f, 0.8f, 1.f), 0.08f, 0.1f, 0.35f), LitMaterial(FLinearColor(0.85f, 0.95f, 1.f), 0.12f, 0.f, 0.25f) };
		for (int32 I = 0; I < 16; ++I)
		{
			FBit& B = AddBit(Cone, Ice[I % 2], 4, R(0.02f, 0.3f), 0.85f - 0.02f, FVector(R(2.5f, 4.5f), R(2.5f, 4.5f), R(9.f, 20.f)));
			B.Grow = 0.22f;
		}
		for (int32 I = 0; I < 54; ++I)
		{
			FBit& B = AddBit(Cube, Ice[I % 2], 0, R(0.85f, 0.9f), R(1.0f, 1.6f), FVector(R(2.f, 5.f), R(1.5f, 3.5f), R(1.5f, 3.5f)));
			B.Vel = FMath::VRandCone(FVector::UpVector, FMath::DegreesToRadians(85.f)) * R(150.f, 460.f);
			B.Gravity = 980.f; B.bBounce = true;
			B.Spin = FRotator(R(-600.f, 600.f), R(-600.f, 600.f), R(-600.f, 600.f));
		}
		if (UMaterialInterface* Shell = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAGlowShell.M_IAGlowShell")))
		{
			UMaterialInstanceDynamic* Mist = UMaterialInstanceDynamic::Create(Shell, this);
			Mist->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.7f, 0.9f, 1.f));
			Mist->SetScalarParameterValue(TEXT("Glow"), 0.35f);
			Mist->SetScalarParameterValue(TEXT("Exponent"), 2.5f);
			Mist->SetScalarParameterValue(TEXT("HideCaps"), 0.f);
			KillMaterials.Add(Mist);
			for (int32 I = 0; I < 4; ++I)
			{
				FBit& B = AddBit(Sphere, Mist, 3, R(0.f, 0.5f), 1.6f, FVector(R(90.f, 140.f)));
				B.Vel = FVector(R(-15.f, 15.f), R(-15.f, 15.f), R(5.f, 20.f));
			}
		}
		break;
	}
	case 4: // Glitch: the body dissolves into jumping coloured pixels.
	{
		FollowUntil = 0.65f;
		FlashColor = FLinearColor(1.f, 0.2f, 0.9f);
		FlashGlow = 2.f;
		LightColor = FLinearColor(0.9f, 0.2f, 1.f);
		LightPeak = 14.f;
		LightLength = 1.0f;
		bLightFlicker = true;
		UMaterialInterface* Pixels[4] = { GlowMaterial(FLinearColor(1.f, 0.1f, 0.85f), 5.f), GlowMaterial(FLinearColor(0.1f, 0.95f, 1.f), 5.f),
			GlowMaterial(FLinearColor(0.4f, 1.f, 0.15f), 4.f), GlowMaterial(VictimColor, 4.f) };
		for (int32 I = 0; I < 70; ++I)
		{
			const float S = R(2.5f, 5.f);
			FBit& B = AddBit(Cube, Pixels[I % 4], 1, R(0.f, 0.6f), R(0.35f, 0.9f), FVector(S, S, S));
			B.Vel = FVector(0.f, 0.f, R(0.f, 30.f));
		}
		for (int32 I = 0; I < 40; ++I)
		{
			const float S = R(2.f, 4.f);
			FBit& B = AddBit(Cube, Pixels[I % 4], 1, R(0.65f, 0.75f), R(0.5f, 1.3f), FVector(S, S, S));
			B.Vel = FVector(0.f, 0.f, R(40.f, 140.f));
		}
		break;
	}
	case 5: // Ember: the body smoulders; glowing embers rise from it for a while.
	{
		FollowUntil = 3.6f;
		FlashColor = FLinearColor(1.f, 0.4f, 0.08f);
		FlashGlow = 2.5f;
		LightColor = FLinearColor(1.f, 0.38f, 0.06f);
		LightPeak = 16.f;
		LightLength = 3.4f;
		bLightFlicker = true;
		UMaterialInterface* Embers[3] = { GlowMaterial(FLinearColor(1.f, 0.35f, 0.04f), 8.f), GlowMaterial(FLinearColor(1.f, 0.14f, 0.02f), 7.f), GlowMaterial(FLinearColor(1.f, 0.62f, 0.12f), 9.f) };
		for (int32 I = 0; I < 70; ++I)
		{
			const float S = R(0.6f, 1.6f);
			FBit& B = AddBit(I % 3 == 0 ? Sphere : Cube, Embers[I % 3], 0, R(0.f, 3.2f), R(0.9f, 1.8f), FVector(S, S, S));
			B.Vel = FVector(R(-30.f, 30.f), R(-30.f, 30.f), R(50.f, 170.f));
			B.Gravity = -90.f; B.Drag = 0.8f;
			B.Spin = FRotator(R(-300.f, 300.f), R(-300.f, 300.f), 0.f);
		}
		for (int32 I = 0; I < 30; ++I)
		{
			const float S = R(0.8f, 1.8f);
			FBit& B = AddBit(Cube, Embers[I % 3], 0, R(3.6f, 3.65f), R(0.7f, 1.3f), FVector(S, S, S));
			B.Vel = FMath::VRandCone(FVector::UpVector, FMath::DegreesToRadians(60.f)) * R(120.f, 320.f);
			B.Gravity = -60.f; B.Drag = 1.2f;
		}
		break;
	}
	case 6: // Poof: a cartoon cloud swallows the body, little stars circle and fly away.
	{
		FollowUntil = 0.f;
		FlashColor = FLinearColor::White;
		FlashGlow = 2.f;
		LightColor = FLinearColor(1.f, 0.95f, 0.8f);
		LightPeak = 12.f;
		LightLength = 0.5f;
		UMaterialInterface* Cloud[2] = { LitMaterial(FLinearColor(0.92f, 0.92f, 0.9f), 1.f, 0.f, 0.15f), LitMaterial(FLinearColor(0.75f, 0.76f, 0.8f), 1.f, 0.f, 0.1f) };
		for (int32 I = 0; I < 11; ++I)
		{
			FBit& B = AddBit(Sphere, Cloud[I % 2], 3, R(0.f, 0.08f), R(0.9f, 1.25f), FVector(R(55.f, 95.f)));
			B.bFromBody = false;
			B.Pos = FVector(R(-38.f, 38.f), R(-38.f, 38.f), R(-55.f, 45.f));
			B.Vel = FVector(B.Pos.X, B.Pos.Y, 30.f) * 0.6f;
		}
		UMaterialInterface* Star = GlowMaterial(FLinearColor(1.f, 0.85f, 0.1f), 4.f);
		for (int32 I = 0; I < 5; ++I)
		{
			const float Angle = I * (2.f * PI / 5.f);
			for (int32 Arm = 0; Arm < 3; ++Arm)
			{
				FBit& B = AddBit(Cube, Star, 2, 0.12f, 1.5f, Arm == 0 ? FVector(9.f, 1.6f, 1.6f) : (Arm == 1 ? FVector(1.6f, 9.f, 1.6f) : FVector(1.6f, 1.6f, 9.f)));
				B.bFromBody = false;
				B.Phase = Angle;
				B.Anchor = FVector(0.f, 0.f, 75.f);
				B.Rot = FRotator(45.f * Arm, 45.f, 0.f);
				B.Spin = FRotator(0.f, 360.f, 0.f);
			}
		}
		break;
	}
	default:
		break;
	}

	// The flash and the light of the moment the effect bursts.
	if (UMaterialInterface* Shell = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/FX/M_IAGlowShell.M_IAGlowShell")))
	{
		FlashMaterial = UMaterialInstanceDynamic::Create(Shell, this);
		FlashMaterial->SetVectorParameterValue(TEXT("Color"), FlashColor);
		FlashMaterial->SetScalarParameterValue(TEXT("Exponent"), 2.4f);
		FlashMaterial->SetScalarParameterValue(TEXT("HideCaps"), 0.f);
		FlashMaterial->SetScalarParameterValue(TEXT("Glow"), 0.f);
		Flash->SetMaterial(0, FlashMaterial);
	}
	Flash->SetVisibility(false);
	Light->SetLightColor(LightColor);
	Light->SetAttenuationRadius(520.f);
}

void AIAImpactEffect::TickKill(float DeltaSeconds)
{
	Age += DeltaSeconds;
	if (Age >= Life)
	{
		Destroy();
		return;
	}
	const float Dt = FMath::Min(DeltaSeconds, 0.05f);

	// Follow the falling body until the effect bursts.
	if (Age < FollowUntil)
	{
		if (const USkeletalMeshComponent* Skel = Body.Get())
		{
			SetActorLocation(Skel->GetBoneLocation(TEXT("pelvis")));
		}
	}

	// The flash: swells and fades in a quarter of a second, at the burst.
	const float FlashT = (Age - FlashDelay) / 0.25f;
	if (FlashMaterial && FlashT >= 0.f && FlashT < 1.f)
	{
		Flash->SetVisibility(true);
		Flash->SetWorldScale3D(FVector((20.f + 70.f * FMath::Sqrt(FlashT)) / 100.f));
		FlashMaterial->SetScalarParameterValue(TEXT("Glow"), FlashGlow * (1.f - FlashT));
	}
	else
	{
		Flash->SetVisibility(false);
	}

	const float LightT = FMath::Clamp((Age - FlashDelay) / LightLength, 0.f, 1.f);
	float Intensity = Age < FlashDelay ? 0.f : LightPeak * (1.f - LightT) * (1.f - LightT);
	if (bLightFlicker)
	{
		Intensity *= 0.6f + 0.4f * FMath::Sin(Age * 37.f) * FMath::Sin(Age * 23.f + 1.f);
	}
	Light->SetIntensity(Intensity);

	for (FBit& Bit : Bits)
	{
		UStaticMeshComponent* Comp = Sparks.IsValidIndex(Bit.Comp) ? Sparks[Bit.Comp].Get() : nullptr;
		if (!Comp || Age < Bit.Birth)
		{
			continue;
		}
		const float T = Age - Bit.Birth;
		if (T >= Bit.Life)
		{
			if (Comp->IsVisible())
			{
				Comp->SetVisibility(false);
			}
			continue;
		}
		if (!Bit.bBorn)
		{
			Bit.bBorn = true;
			const FVector Base = Bit.bFromBody ? RandomBodyPoint() : GetActorLocation();
			Bit.Pos = Base + Bit.Pos;
			Bit.Anchor = Base + Bit.Anchor;
			if (Bit.Kind == 4)
			{
				// A spike points away from the middle of the body.
				const FVector Out = (Bit.Pos - GetActorLocation()).GetSafeNormal() + FMath::VRand() * 0.5f;
				Bit.Rot = FRotationMatrix::MakeFromZ(Out.GetSafeNormal()).Rotator();
			}
			Comp->SetVisibility(true);
		}

		float SizeScale = 1.f;
		if (Bit.Grow > 0.f)
		{
			SizeScale *= FMath::Clamp(T / Bit.Grow, 0.f, 1.f);
		}
		const float Remaining = Bit.Life - T;
		SizeScale *= FMath::Clamp(Remaining / (0.3f * Bit.Life), 0.f, 1.f);
		FVector Where = Bit.Pos;
		FVector Size = Bit.Size;

		switch (Bit.Kind)
		{
		case 1: // glitch voxel: jumps to a new spot near its anchor every few hundredths of a second, sometimes smeared sideways
		{
			Bit.Anchor.Z += Bit.Vel.Z * Dt;
			if (T >= Bit.NextJump)
			{
				Bit.NextJump = T + FMath::FRandRange(0.03f, 0.11f);
				Bit.Pos = Bit.Anchor + FVector(FMath::FRandRange(-7.f, 7.f), FMath::FRandRange(-7.f, 7.f), FMath::FRandRange(-4.f, 4.f));
				Bit.Phase = FMath::FRand() < 0.2f ? 4.f : 1.f;
			}
			Where = Bit.Pos;
			Size.X *= Bit.Phase;
			Bit.Rot = FRotator::ZeroRotator;
			const bool bShown = FMath::Frac(T * 11.f + Bit.Phase * 0.37f) > 0.22f;
			if (Comp->IsVisible() != bShown)
			{
				Comp->SetVisibility(bShown);
			}
			SizeScale = 1.f;
			break;
		}
		case 2: // star: circles over the cloud, then flies away
		{
			const float Out = FMath::Max(0.f, T - 1.0f) * 260.f;
			const float Angle = Bit.Phase + T * 4.2f;
			Where = Bit.Anchor + FVector(FMath::Cos(Angle) * (34.f + Out), FMath::Sin(Angle) * (34.f + Out), FMath::Sin(T * 7.f + Bit.Phase) * 5.f + Out * 0.4f);
			Bit.Rot += Bit.Spin * Dt;
			SizeScale = FMath::Clamp(T / 0.15f, 0.f, 1.f) * FMath::Clamp(Remaining / 0.3f, 0.f, 1.f);
			break;
		}
		case 3: // puff: swells fast, drifts, then shrinks away
		{
			Bit.Pos += Bit.Vel * Dt;
			Bit.Vel *= FMath::Max(0.f, 1.f - 2.f * Dt);
			Where = Bit.Pos;
			const float In = 1.f - FMath::Pow(1.f - FMath::Clamp(T / 0.22f, 0.f, 1.f), 3.f);
			const float OutT = FMath::Clamp((T - Bit.Life * 0.45f) / (Bit.Life * 0.55f), 0.f, 1.f);
			SizeScale = (0.25f + 0.75f * In) * (1.f - OutT * OutT);
			break;
		}
		case 4: // spike: grows out of the body and stays
		{
			SizeScale = FMath::Clamp(T / FMath::Max(Bit.Grow, 0.01f), 0.f, 1.f);
			Where = Bit.Pos + Bit.Rot.RotateVector(FVector(0.f, 0.f, Size.Z * SizeScale * 0.5f));
			break;
		}
		default: // debris: flies, falls (or rises), slows in the air and bounces on the floor
		{
			Bit.Vel.Z -= Bit.Gravity * Dt;
			Bit.Vel *= FMath::Max(0.f, 1.f - Bit.Drag * Dt);
			Bit.Pos += Bit.Vel * Dt;
			if (Bit.bBounce && Bit.Pos.Z < FloorZ)
			{
				Bit.Pos.Z = FloorZ;
				Bit.Vel.Z = FMath::Abs(Bit.Vel.Z) * 0.3f;
				Bit.Vel.X *= 0.55f;
				Bit.Vel.Y *= 0.55f;
				Bit.Spin *= 0.5f;
			}
			Bit.Rot += Bit.Spin * Dt;
			Where = Bit.Pos;
			break;
		}
		}
		Comp->SetWorldLocationAndRotation(Where, Bit.Rot);
		Comp->SetWorldScale3D(Size * FMath::Max(SizeScale, 0.001f) / 100.f);
	}
}
