// Instagib Arena

#include "IACharacterGear.h"
#include "IACharacterRoster.h"
#include "InstagibArena.h"
#include "AnimationRuntime.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

int32 IAGear::Attach(AActor* Owner, USkeletalMeshComponent* Skel, USkeletalMesh* MeshAsset, int32 LookIndex, const FIACharacterLook& Look,
	const FLinearColor& Body, const FLinearColor& AccentPaint, const FLinearColor& Accent, const FLinearColor& TeamColor, bool bTeamGame,
	float RimStrength, TArray<TObjectPtr<UStaticMeshComponent>>& OutComponents)
{
	const TArray<FIAGearPiece>& Gear = IACharacters::GetGear(LookIndex);
	if (Gear.Num() == 0 || !Skel || !MeshAsset || !Owner)
	{
		return 0;
	}
	UMaterialInterface* BaseMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Characters/Gear/M_IAGear.M_IAGear"));
	if (!BaseMaterial)
	{
		UE_LOG(LogInstagib, Warning, TEXT("Gear: M_IAGear is missing, using the primitive accessories"));
		return 0;
	}

	// The palette. Roles: 0 plate (suit colour), 1 cloth, 2 accent paint, 3 team, 4 trim (dark metal), 5 glow (visors, eyes), 6 light.
	const bool bHologram = Look.BodyGlow > 0.f;
	const bool bMetalAccent = Look.AccentMetal > 0.f;
	const FLinearColor Cloth = Look.GearCloth.A > 0.f ? FLinearColor(Look.GearCloth.R, Look.GearCloth.G, Look.GearCloth.B) : Body * 0.62f;
	struct FRole { FLinearColor Color; float Roughness; float Metal; };
	FRole Roles[7] = {
		{ Body,                                       FMath::Clamp(Look.Roughness, 0.5f, 0.9f), Look.Metallic },
		{ Cloth,                                      0.9f,                                       0.f },
		{ AccentPaint,                                bMetalAccent ? 0.35f : 0.6f,                Look.AccentMetal },
		{ TeamColor,                                  0.55f,                                      0.f },
		{ FLinearColor(0.05f, 0.055f, 0.065f),        0.5f,                                       0.6f },
		{ Accent,                                     0.4f,                                       0.f },
		{ FLinearColor(0.8f, 0.8f, 0.76f),            0.9f,                                       0.f },
	};
	// Per-look overrides (glossy obsidian plate, a red glow beside a gold accent, a matte glow role ...).
	float GlowStrength = 2.0f;
	for (const FIAGearRole& Override : Look.GearRoles)
	{
		if (Override.Role < 0 || Override.Role >= 7)
		{
			continue;
		}
		FRole& R = Roles[Override.Role];
		if (Override.Color.A > 0.f) { R.Color = FLinearColor(Override.Color.R, Override.Color.G, Override.Color.B); }
		if (Override.Roughness >= 0.f) { R.Roughness = Override.Roughness; }
		if (Override.Metal >= 0.f) { R.Metal = Override.Metal; }
		if (Override.Role == 5 && Override.Glow >= 0.f) { GlowStrength = Override.Glow; }
	}
	UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, Owner);
	for (int32 I = 0; I < 7; ++I)
	{
		Material->SetVectorParameterValue(*FString::Printf(TEXT("C%d"), I), FLinearColor(Roles[I].Color.R, Roles[I].Color.G, Roles[I].Color.B, Roles[I].Roughness));
		Material->SetScalarParameterValue(*FString::Printf(TEXT("Metal%d"), I), Roles[I].Metal);
	}
	Material->SetScalarParameterValue(TEXT("Glow"), GlowStrength);                   // visors and eyes only (role 5)
	Material->SetScalarParameterValue(TEXT("TeamGlow"), bTeamGame ? 0.5f : 0.f);    // keeps the team colour readable in the shade
	Material->SetScalarParameterValue(TEXT("Rim"), RimStrength);
	Material->SetVectorParameterValue(TEXT("RimColor"), TeamColor);
	(void)bHologram;

	const FReferenceSkeleton& RefSkeleton = MeshAsset->GetRefSkeleton();
	const FQuat MeshToActor = FRotator(0.f, -90.f, 0.f).Quaternion(); // the mesh component's rotation inside the actor

	int32 Count = 0;
	for (const FIAGearPiece& Piece : Gear)
	{
		const int32 BoneIndex = RefSkeleton.FindBoneIndex(Piece.Bone);
		if (BoneIndex == INDEX_NONE)
		{
			UE_LOG(LogInstagib, Warning, TEXT("Gear %s: bone %s not found"), Look.Name, Piece.Bone);
			continue;
		}
		UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, Piece.Mesh, nullptr, LOAD_NoWarn);
		if (!Mesh)
		{
			UE_LOG(LogInstagib, Warning, TEXT("Gear %s: mesh %s is missing"), Look.Name, Piece.Mesh);
			continue;
		}

		// The mesh is authored in character space (X forward, Y right, Z up) around the bone origin: only the bone's own orientation
		// in the reference pose has to be undone, like for the primitive accessories.
		const FTransform BoneInMesh = FAnimationRuntime::GetComponentSpaceTransformRefPose(RefSkeleton, BoneIndex);
		const FQuat LocalRotation = BoneInMesh.GetRotation().Inverse() * MeshToActor.Inverse();

		UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(Owner);
		Comp->SetStaticMesh(Mesh);
		for (int32 Slot = 0; Slot < Comp->GetNumMaterials(); ++Slot)
		{
			Comp->SetMaterial(Slot, Material);
		}
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetOwnerNoSee(true);
		Comp->SetCastShadow(false);
		Comp->SetRelativeLocationAndRotation(FVector::ZeroVector, LocalRotation.Rotator());
		Comp->RegisterComponent();
		Comp->AttachToComponent(Skel, FAttachmentTransformRules::KeepRelativeTransform, Piece.Bone);
		OutComponents.Add(Comp);
		++Count;
	}
	return Count;
}
