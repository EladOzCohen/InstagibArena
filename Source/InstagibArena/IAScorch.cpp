// Instagib Arena

#include "IAScorch.h"
#include "Components/DecalComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

bool UIAScorchSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->IsGameWorld() && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

UIAScorchSubsystem* UIAScorchSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<UIAScorchSubsystem>() : nullptr;
}

void UIAScorchSubsystem::AddMark(const FVector& Location, const FVector& Normal, const FLinearColor& Color)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	if (!BaseMaterial)
	{
		BaseMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Materials/M_Scorch.M_Scorch"));
		if (!BaseMaterial)
		{
			return;
		}
	}

	// The pool is full: the oldest mark goes.
	Marks.RemoveAll([](const FMark& Mark) { return !Mark.Decal.IsValid(); });
	while (Marks.Num() >= MaxMarks)
	{
		if (UDecalComponent* Old = Marks[0].Decal.Get())
		{
			Old->DestroyComponent();
		}
		Marks.RemoveAt(0);
	}

	// The decal projects along its X axis, into the wall. A random turn around that axis varies the look.
	const FRotator Rotation = (FRotationMatrix::MakeFromX(-Normal).ToQuat() * FQuat(FVector::ForwardVector, FMath::FRandRange(0.f, TWO_PI))).Rotator();
	const float Size = FMath::FRandRange(11.f, 16.f);
	UDecalComponent* Decal = UGameplayStatics::SpawnDecalAtLocation(World, BaseMaterial, FVector(14.f, Size, Size), Location, Rotation, 0.f);
	if (!Decal)
	{
		return;
	}
	Decal->SetFadeScreenSize(0.f);

	FMark Mark;
	Mark.Decal = Decal;
	Mark.Material = Decal->CreateDynamicMaterialInstance();
	if (UMaterialInstanceDynamic* Material = Mark.Material.Get())
	{
		Material->SetVectorParameterValue(TEXT("Color"), Color);
		Material->SetScalarParameterValue(TEXT("Glow"), 1.f);
		Material->SetScalarParameterValue(TEXT("Alpha"), 1.f);
	}
	Marks.Add(Mark);
}

void UIAScorchSubsystem::Tick(float DeltaTime)
{
	for (int32 I = Marks.Num() - 1; I >= 0; --I)
	{
		FMark& Mark = Marks[I];
		Mark.Age += DeltaTime;
		UDecalComponent* Decal = Mark.Decal.Get();
		if (!Decal || Mark.Age >= Lifetime)
		{
			if (Decal)
			{
				Decal->DestroyComponent();
			}
			Marks.RemoveAtSwap(I);
			continue;
		}
		if (UMaterialInstanceDynamic* Material = Mark.Material.Get())
		{
			// Hot for a second or two, then the mark just darkens and fades in the last seconds.
			const float Glow = FMath::Exp(-Mark.Age * 1.1f);
			const float Alpha = FMath::Clamp((Lifetime - Mark.Age) / 8.f, 0.f, 1.f);
			Material->SetScalarParameterValue(TEXT("Glow"), Glow);
			Material->SetScalarParameterValue(TEXT("Alpha"), Alpha);
		}
	}
}
