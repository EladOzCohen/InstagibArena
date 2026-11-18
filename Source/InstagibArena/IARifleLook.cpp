// Instagib Arena

#include "IARifleLook.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
	// ---------------------------------------------------------------- the palette of the six slots

	struct FSlotLook
	{
		FLinearColor Color;
		float Roughness;
		float Metallic;
	};

	/** What the loadout makes of the rifle's slots. Starts from the values of Tools/make_weapon_assets.py (SLOTS). */
	struct FPalette
	{
		FSlotLook Body { FLinearColor(0.15f, 0.155f, 0.17f), 0.42f, 0.5f };
		FSlotLook Trim { FLinearColor(0.06f, 0.065f, 0.072f), 0.52f, 0.5f };
		FSlotLook Paint { FLinearColor(0.55f, 0.30f, 0.04f), 0.48f, 0.25f };
		FLinearColor Core = FLinearColor::White;
		float Detail = 1.f;
	};

	const FLinearColor GoldColor(1.0f, 0.70f, 0.28f);

	FLinearColor Lin(const FColor& C)
	{
		return FLinearColor::FromSRGBColor(C);
	}

	FPalette MakePalette(const FIACosmeticLoadout& L, const FLinearColor& Accent)
	{
		FPalette P;
		P.Paint.Color = Accent * 0.7f;
		P.Core = Accent;

		// Faction liveries: their own colours (the parts come in AddParts).
		switch (L.RifleLivery)
		{
		case 1: // Rustborn: rusted iron, orange paint
			P.Body = { FLinearColor(0.20f, 0.085f, 0.035f), 0.78f, 0.35f };
			P.Trim = { FLinearColor(0.07f, 0.06f, 0.05f), 0.7f, 0.55f };
			P.Paint = { FLinearColor(0.85f, 0.32f, 0.04f), 0.6f, 0.2f };
			P.Core = FLinearColor(1.f, 0.42f, 0.06f);
			break;
		case 2: // Legion: crimson lacquer and gold
			P.Body = { FLinearColor(0.24f, 0.018f, 0.02f), 0.32f, 0.45f };
			P.Trim = { GoldColor * 0.8f, 0.28f, 1.f };
			P.Paint = { GoldColor, 0.25f, 1.f };
			P.Core = FLinearColor(1.f, 0.6f, 0.15f);
			break;
		case 3: // Syndicate: black gloss and neon
			P.Body = { FLinearColor(0.012f, 0.012f, 0.016f), 0.16f, 0.35f };
			P.Trim = { FLinearColor(0.03f, 0.03f, 0.04f), 0.25f, 0.6f };
			P.Paint = { FLinearColor(0.9f, 0.04f, 0.55f), 0.3f, 0.1f };
			P.Core = FLinearColor(0.05f, 0.85f, 1.f);
			break;
		case 4: // Void Corps: white pressure suit
			P.Body = { FLinearColor(0.72f, 0.74f, 0.78f), 0.45f, 0.05f };
			P.Trim = { FLinearColor(0.22f, 0.23f, 0.25f), 0.5f, 0.3f };
			P.Paint = { FLinearColor(0.06f, 0.10f, 0.20f), 0.5f, 0.1f };
			P.Core = FLinearColor(0.45f, 0.85f, 1.f);
			break;
		case 5: // Hollow Court: bone and black, violet light
			P.Body = { FLinearColor(0.42f, 0.37f, 0.29f), 0.68f, 0.05f };
			P.Trim = { FLinearColor(0.02f, 0.018f, 0.02f), 0.5f, 0.4f };
			P.Paint = { FLinearColor(0.20f, 0.03f, 0.30f), 0.5f, 0.1f };
			P.Core = FLinearColor(0.6f, 0.1f, 1.f);
			break;
		case 6: // Obsidian: volcanic glass, gold, red light
			P.Body = { FLinearColor(0.012f, 0.012f, 0.015f), 0.18f, 0.8f };
			P.Trim = { GoldColor * 0.85f, 0.25f, 1.f };
			P.Paint = { GoldColor, 0.22f, 1.f };
			P.Core = FLinearColor(1.f, 0.05f, 0.02f);
			break;
		default:
			break;
		}

		// Finishes: the surface of the body and the dark steel.
		switch (L.RifleFinish)
		{
		case 1: // matt
			P.Body.Roughness = 0.88f; P.Body.Metallic = 0.08f;
			P.Trim.Roughness = 0.85f; P.Trim.Metallic = 0.1f;
			P.Detail = 0.4f;
			break;
		case 2: // polished steel
			P.Body = { FLinearColor(0.60f, 0.61f, 0.64f), 0.12f, 1.f };
			P.Trim = { FLinearColor(0.28f, 0.29f, 0.31f), 0.2f, 1.f };
			P.Detail = 0.35f;
			break;
		case 3: // brushed brass
			P.Body = { FLinearColor(0.78f, 0.55f, 0.24f), 0.34f, 1.f };
			P.Trim = { FLinearColor(0.32f, 0.22f, 0.09f), 0.4f, 1.f };
			break;
		case 4: // gold (Master Gunsmith)
			P.Body = { GoldColor, 0.2f, 1.f };
			P.Trim = { GoldColor * 0.55f, 0.26f, 1.f };
			P.Paint = { FLinearColor(0.9f, 0.82f, 0.62f), 0.18f, 1.f };
			P.Detail = 0.25f;
			break;
		default:
			break;
		}

		// Free colours (the Gunsmith proper). Gold stays gold; on the other finishes the colour takes the finish's surface.
		if (L.bCustomRifle)
		{
			if (L.RifleFinish != 4)
			{
				P.Body.Color = Lin(L.RifleBody);
			}
			P.Paint.Color = Lin(L.RifleAccent) * 0.85f;
			P.Core = Lin(L.RifleCore);
		}
		return P;
	}

	// ---------------------------------------------------------------- the extra parts

	/** Adds boxes, cylinders, spheres and cones to the rifle; one instanced component per shape and material. */
	class FPartBuilder
	{
	public:
		FPartBuilder(AActor* InOwner, USceneComponent* InRoot, bool bInFirstPerson, UMaterialInterface* InBase, TArray<TObjectPtr<UStaticMeshComponent>>& InOut)
			: Owner(InOwner), Root(InRoot), bFirstPerson(bInFirstPerson), Base(InBase), Out(InOut)
		{
			static const TCHAR* const Paths[4] = {
				TEXT("/Engine/BasicShapes/Cube.Cube"), TEXT("/Engine/BasicShapes/Cylinder.Cylinder"),
				TEXT("/Engine/BasicShapes/Sphere.Sphere"), TEXT("/Engine/BasicShapes/Cone.Cone") };
			for (int32 I = 0; I < 4; ++I)
			{
				Meshes[I] = LoadObject<UStaticMesh>(nullptr, Paths[I]);
			}
		}

		enum EShape { Cube, Cylinder, Sphere, Cone };

		/** A material of the rifle's master: colour, surface and an optional glow (the emissive colour is the same colour). */
		UMaterialInstanceDynamic* Mat(const FLinearColor& Color, float Roughness, float Metallic, float Glow = 0.f)
		{
			const FString Key = FString::Printf(TEXT("%.3f,%.3f,%.3f,%.2f,%.2f,%.2f"), Color.R, Color.G, Color.B, Roughness, Metallic, Glow);
			if (UMaterialInstanceDynamic** Found = Materials.Find(Key))
			{
				return *Found;
			}
			UMaterialInstanceDynamic* M = UMaterialInstanceDynamic::Create(Base, Owner);
			M->SetVectorParameterValue(TEXT("BodyColor"), Glow > 0.f ? Color * 0.15f : Color);
			M->SetVectorParameterValue(TEXT("AccentColor"), Color);
			M->SetScalarParameterValue(TEXT("Glow"), Glow);
			M->SetScalarParameterValue(TEXT("Roughness"), Roughness);
			M->SetScalarParameterValue(TEXT("Metallic"), Metallic);
			M->SetScalarParameterValue(TEXT("Detail"), 0.f);
			// The same values for the fallback material (M_IACharacter / M_IABody use other names).
			M->SetVectorParameterValue(TEXT("Color"), Color);
			Materials.Add(Key, M);
			return M;
		}

		UMaterialInstanceDynamic* Mat(const FSlotLook& Look, float Glow = 0.f)
		{
			return Mat(Look.Color, Look.Roughness, Look.Metallic, Glow);
		}

		void Add(EShape Shape, UMaterialInterface* Material, const FTransform& Transform)
		{
			if (!Meshes[Shape] || !Material)
			{
				return;
			}
			const TPair<int32, UMaterialInterface*> Key(static_cast<int32>(Shape), Material);
			UInstancedStaticMeshComponent* Batch = Batches.FindRef(Key);
			if (!Batch)
			{
				Batch = NewObject<UInstancedStaticMeshComponent>(Owner);
				Batch->SetStaticMesh(Meshes[Shape]);
				Batch->SetMaterial(0, Material);
				Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Batch->SetCastShadow(false);
				Batch->SetCanEverAffectNavigation(false);
				if (bFirstPerson)
				{
					Batch->SetOnlyOwnerSee(true);
				}
				else
				{
					Batch->SetOwnerNoSee(true);
				}
				Batch->SetRelativeTransform(FTransform::Identity);
				Batch->RegisterComponent();
				Batch->AttachToComponent(Root, FAttachmentTransformRules::KeepRelativeTransform);
				Batches.Add(Key, Batch);
				Out.Add(Batch);
			}
			Batch->AddInstance(Transform, /*bWorldSpace*/ false);
		}

		/** A shape of the given size in cm (cylinders and cones: diameter, diameter, length along their Z), centred at Location. */
		void Part(EShape Shape, UMaterialInterface* Material, const FVector& Location, const FVector& Size, const FRotator& Rotation = FRotator::ZeroRotator)
		{
			Add(Shape, Material, FTransform(Rotation, Location, Size / 100.f));
		}

		/** The same inside a local frame (for pieces that sit on a tilted panel). */
		void PartIn(const FTransform& Frame, EShape Shape, UMaterialInterface* Material, const FVector& Location, const FVector& Size, const FRotator& Rotation = FRotator::ZeroRotator)
		{
			Add(Shape, Material, FTransform(Rotation, Location, Size / 100.f) * Frame);
		}

		/** A box from Min to Max (rifle space). */
		void Box(UMaterialInterface* Material, const FVector& Min, const FVector& Max, const FRotator& Rotation = FRotator::ZeroRotator)
		{
			Part(Cube, Material, (Min + Max) * 0.5f, (Max - Min).GetAbs(), Rotation);
		}

		/** A cylinder (or cone) from A to B with the given diameter. A cone points from A to B. */
		void Rod(UMaterialInterface* Material, const FVector& A, const FVector& B, float Diameter, EShape Shape = Cylinder)
		{
			const FVector Axis = B - A;
			const float Length = Axis.Size();
			if (Length < 0.01f)
			{
				return;
			}
			Part(Shape, Material, (A + B) * 0.5f, FVector(Diameter, Diameter, Length), FRotationMatrix::MakeFromZ(Axis).Rotator());
		}

		/** A ring-like disc around the barrel axis (a short cylinder along X). */
		void Collar(UMaterialInterface* Material, float X, float Width, float Diameter, float Z = 0.5f)
		{
			Part(Cylinder, Material, FVector(X, 0.f, Z), FVector(Diameter, Diameter, Width), FRotator(-90.f, 0.f, 0.f));
		}

	private:
		AActor* Owner;
		USceneComponent* Root;
		bool bFirstPerson;
		UMaterialInterface* Base;
		TArray<TObjectPtr<UStaticMeshComponent>>& Out;
		UStaticMesh* Meshes[4] = { nullptr, nullptr, nullptr, nullptr };
		TMap<FString, UMaterialInstanceDynamic*> Materials;
		TMap<TPair<int32, UMaterialInterface*>, UInstancedStaticMeshComponent*> Batches;
	};

	using EShape = FPartBuilder::EShape;
	constexpr float BarrelZ = 0.5f;   // height of the barrel axis (Tools/mesh_weapon.py BARREL_Z)

	/** Segments of a seven-segment digit: a top, b top right, c bottom right, d bottom, e bottom left, f top left, g middle. */
	const uint8 DigitSegments[10] = {
		0b0111111, 0b0000110, 0b1011011, 0b1001111, 0b1100110, 0b1101101, 0b1111101, 0b0000111, 0b1111111, 0b1101111 };

	void AddBarrel(FPartBuilder& B, const FIACosmeticLoadout& L, const FPalette& P)
	{
		UMaterialInterface* Body = B.Mat(P.Body);
		UMaterialInterface* Trim = B.Mat(P.Trim);
		UMaterialInterface* Paint = B.Mat(P.Paint);
		UMaterialInterface* Core = B.Mat(P.Core, 0.3f, 0.f, 3.f);
		switch (L.Barrel)
		{
		case 1: // short: a heavy heat shroud over the emitter coils
			B.Collar(Body, 51.f, 13.6f, 9.2f);
			for (const float X : { 46.8f, 50.6f, 54.4f })
			{
				B.Collar(Trim, X, 0.7f, 9.5f);
			}
			B.Collar(Trim, 58.f, 1.2f, 9.8f);
			B.Collar(Paint, 44.6f, 0.8f, 9.6f);
			break;
		case 2: // long: an extension with a muzzle brake
			B.Collar(Trim, 68.f, 9.f, 4.2f);
			B.Box(Body, FVector(71.f, -2.9f, BarrelZ - 2.9f), FVector(76.f, 2.9f, BarrelZ + 2.9f));
			for (const float S : { -1.f, 1.f })
			{
				B.Box(Trim, FVector(72.f, 2.8f * S, BarrelZ - 2.f), FVector(73.f, 3.05f * S, BarrelZ + 2.f));
				B.Box(Trim, FVector(74.f, 2.8f * S, BarrelZ - 2.f), FVector(75.f, 3.05f * S, BarrelZ + 2.f));
			}
			B.Collar(Core, 76.2f, 0.4f, 2.6f);
			B.Collar(Paint, 65.f, 0.8f, 4.8f);
			break;
		case 3: // twin: a second emitter tube over the first
			B.Rod(Trim, FVector(30.f, 0.f, 6.6f), FVector(62.f, 0.f, 6.6f), 2.6f);
			B.Rod(Core, FVector(62.f, 0.f, 6.6f), FVector(62.6f, 0.f, 6.6f), 1.7f);
			for (const float X : { 33.f, 52.f, 60.f })
			{
				B.Box(Body, FVector(X - 0.8f, -1.1f, 3.6f), FVector(X + 0.8f, 1.1f, 6.4f));
			}
			B.Collar(Paint, 47.f, 1.f, 3.2f, 6.6f);
			break;
		case 4: // pennant: a little flag on a pole over the muzzle (Flagbearer)
		{
			B.Rod(Trim, FVector(57.f, 0.f, 3.4f), FVector(57.f, 0.f, 16.f), 0.5f);
			B.Part(EShape::Sphere, B.Mat(GoldColor, 0.25f, 1.f), FVector(57.f, 0.f, 16.3f), FVector(1.1f));
			// A triangle that points back, made of steps.
			const float Steps[4][2] = { { 15.4f, 8.f }, { 14.4f, 6.f }, { 13.4f, 4.f }, { 12.4f, 2.f } };
			for (const auto& Step : Steps)
			{
				B.Box(Paint, FVector(57.f - Step[1], -0.12f, Step[0] - 1.f), FVector(57.f, 0.12f, Step[0]));
			}
			B.Box(B.Mat(FLinearColor(0.85f, 0.85f, 0.82f), 0.8f, 0.f), FVector(52.f, -0.15f, 13.6f), FVector(55.f, 0.15f, 14.2f));
			break;
		}
		default:
			break;
		}
	}

	void AddStock(FPartBuilder& B, const FIACosmeticLoadout& L, const FPalette& P)
	{
		UMaterialInterface* Body = B.Mat(P.Body);
		UMaterialInterface* Trim = B.Mat(P.Trim);
		UMaterialInterface* Paint = B.Mat(P.Paint);
		UMaterialInterface* Rubber = B.Mat(FLinearColor(0.045f, 0.045f, 0.05f), 0.86f, 0.f);
		switch (L.Stock)
		{
		case 1: // skeleton: an open frame of rods
			for (const float S : { -1.f, 1.f })
			{
				B.Rod(Trim, FVector(-9.f, 2.6f * S, 3.f), FVector(-25.f, 2.4f * S, 2.f), 1.3f);
				B.Rod(Trim, FVector(-9.f, 2.6f * S, -3.f), FVector(-25.f, 2.4f * S, -8.5f), 1.3f);
				B.Rod(Trim, FVector(-18.f, 2.5f * S, 2.5f), FVector(-18.f, 2.5f * S, -5.8f), 1.f);
			}
			B.Box(Rubber, FVector(-27.f, -2.9f, -10.f), FVector(-25.f, 2.9f, 3.4f));
			B.Box(Paint, FVector(-25.4f, -3.f, -1.f), FVector(-24.9f, 3.f, 1.f));
			break;
		case 2: // heavy: a solid block
			B.Box(Body, FVector(-24.f, -2.6f, -8.5f), FVector(-10.f, 2.6f, 3.4f));
			B.Box(Rubber, FVector(-26.f, -2.8f, -9.f), FVector(-24.f, 2.8f, 3.8f));
			B.Box(Paint, FVector(-22.f, -2.75f, -1.2f), FVector(-12.f, 2.75f, 0.f));
			break;
		case 3: // marksman: cheek riser, adjustable butt, a spike
			B.Box(Paint, FVector(-22.f, -1.8f, 3.4f), FVector(-12.f, 1.8f, 5.6f));
			for (const float S : { -1.f, 1.f })
			{
				B.Rod(Trim, FVector(-22.f, 1.5f * S, -2.f), FVector(-29.f, 1.5f * S, -2.f), 0.9f);
			}
			B.Box(Rubber, FVector(-30.5f, -2.6f, -10.f), FVector(-29.f, 2.6f, 3.f));
			B.Rod(Body, FVector(-20.f, 0.f, -8.f), FVector(-20.f, 0.f, -13.f), 1.f);
			B.Rod(Trim, FVector(-20.f, 0.f, -13.f), FVector(-20.f, 0.f, -14.5f), 1.f, EShape::Cone);
			break;
		default:
			break;
		}
	}

	void AddFins(FPartBuilder& B, const FIACosmeticLoadout& L, const FPalette& P)
	{
		if (L.Fins == 0)
		{
			return;
		}
		const bool bIon = L.Fins == 2;
		UMaterialInterface* Fin = bIon ? B.Mat(P.Paint) : B.Mat(P.Body);
		UMaterialInterface* Edge = B.Mat(P.Core, 0.3f, 0.f, 4.f);
		// Radial heat-sink fins on both sides of the handguard, swept back a little.
		for (const float S : { -1.f, 1.f })
		{
			for (const float Angle : { -22.f, 0.f, 22.f })
			{
				const float Rad = FMath::DegreesToRadians(Angle);
				const FVector Out(0.f, FMath::Cos(Rad) * S, FMath::Sin(Rad));
				const float Inner = 4.3f;
				const float Outer = bIon ? 7.4f : 6.8f;
				const FVector Centre = FVector(37.f, 0.f, BarrelZ) + Out * ((Inner + Outer) * 0.5f);
				const FRotator Roll(0.f, 0.f, Angle * S);
				B.Part(EShape::Cube, Fin, Centre, FVector(13.f, Outer - Inner, 0.35f), Roll);
				if (bIon)
				{
					B.Part(EShape::Cube, Edge, FVector(37.f, 0.f, BarrelZ) + Out * (Outer + 0.1f), FVector(12.f, 0.25f, 0.4f), Roll);
				}
			}
		}
	}

	void AddCharm(FPartBuilder& B, const FIACosmeticLoadout& L, const FPalette& P)
	{
		// On the top rail at the back, where the player sees it.
		const FVector Seat(-3.5f, 0.f, 5.25f);
		switch (L.Charm)
		{
		case 1: // a tiny top hat
		{
			UMaterialInterface* Felt = B.Mat(FLinearColor(0.015f, 0.015f, 0.018f), 0.75f, 0.f);
			const FRotator Tilt(0.f, 0.f, -10.f);
			B.Part(EShape::Cylinder, Felt, Seat + FVector(0.f, 0.f, 0.25f), FVector(6.f, 6.f, 0.5f), Tilt);
			B.Part(EShape::Cylinder, Felt, Seat + FVector(0.f, 0.35f, 2.4f), FVector(3.8f, 3.8f, 4.f), Tilt);
			B.Part(EShape::Cylinder, B.Mat(FLinearColor(0.5f, 0.02f, 0.03f), 0.6f, 0.f), Seat + FVector(0.f, 0.12f, 1.0f), FVector(3.95f, 3.95f, 0.8f), Tilt);
			break;
		}
		case 2: // a rubber duck, looking at the player
		{
			UMaterialInterface* Yellow = B.Mat(FLinearColor(1.f, 0.72f, 0.02f), 0.35f, 0.f);
			B.Part(EShape::Sphere, Yellow, Seat + FVector(0.f, 0.f, 1.8f), FVector(5.f, 4.f, 3.4f));
			B.Part(EShape::Sphere, Yellow, Seat + FVector(-1.6f, 0.f, 4.3f), FVector(2.8f));
			B.Part(EShape::Sphere, Yellow, Seat + FVector(2.4f, 0.f, 2.8f), FVector(1.6f, 1.4f, 1.8f));   // tail
			B.Part(EShape::Cube, B.Mat(FLinearColor(1.f, 0.25f, 0.02f), 0.4f, 0.f), Seat + FVector(-3.1f, 0.f, 4.1f), FVector(1.5f, 1.3f, 0.6f));
			UMaterialInterface* Eye = B.Mat(FLinearColor(0.01f, 0.01f, 0.01f), 0.2f, 0.f);
			for (const float S : { -1.f, 1.f })
			{
				B.Part(EShape::Sphere, Eye, Seat + FVector(-2.6f, 0.75f * S, 4.8f), FVector(0.5f));
			}
			break;
		}
		case 3: // a tiny cow, looking at the player
		{
			UMaterialInterface* White = B.Mat(FLinearColor(0.85f, 0.85f, 0.82f), 0.7f, 0.f);
			UMaterialInterface* Black = B.Mat(FLinearColor(0.02f, 0.02f, 0.02f), 0.7f, 0.f);
			UMaterialInterface* Pink = B.Mat(FLinearColor(0.9f, 0.4f, 0.45f), 0.6f, 0.f);
			B.Part(EShape::Cube, White, Seat + FVector(0.5f, 0.f, 2.8f), FVector(5.f, 2.8f, 2.6f));
			B.Part(EShape::Cube, Black, Seat + FVector(1.2f, 1.42f, 3.2f), FVector(2.f, 0.1f, 1.4f));
			B.Part(EShape::Cube, Black, Seat + FVector(-0.6f, -1.42f, 2.4f), FVector(1.6f, 0.1f, 1.2f));
			B.Part(EShape::Cube, Black, Seat + FVector(1.8f, 0.f, 4.12f), FVector(1.6f, 1.4f, 0.1f));
			B.Part(EShape::Cube, White, Seat + FVector(-2.6f, 0.f, 3.9f), FVector(1.9f, 2.f, 1.9f));
			B.Part(EShape::Cube, Pink, Seat + FVector(-3.6f, 0.f, 3.5f), FVector(0.5f, 1.6f, 0.9f));
			for (const float S : { -1.f, 1.f })
			{
				B.Rod(B.Mat(FLinearColor(0.8f, 0.75f, 0.6f), 0.5f, 0.f), Seat + FVector(-2.6f, 0.7f * S, 4.8f), Seat + FVector(-2.8f, 1.5f * S, 5.8f), 0.45f, EShape::Cone);
				B.Rod(Black, Seat + FVector(-1.4f, 1.1f * S, 1.5f), Seat + FVector(-1.4f, 1.1f * S, 0.f), 0.7f);
				B.Rod(Black, Seat + FVector(2.4f, 1.1f * S, 1.5f), Seat + FVector(2.4f, 1.1f * S, 0.f), 0.7f);
			}
			B.Rod(White, Seat + FVector(3.f, 0.f, 3.5f), Seat + FVector(3.8f, 0.f, 1.6f), 0.3f);
			break;
		}
		default:
			break;
		}
	}

	void AddLivery(FPartBuilder& B, const FIACosmeticLoadout& L, const FPalette& P)
	{
		switch (L.RifleLivery)
		{
		case 1: // Rustborn: welded plates with beads and rivets
		{
			UMaterialInterface* Plate = B.Mat(FLinearColor(0.16f, 0.07f, 0.03f), 0.85f, 0.4f);
			UMaterialInterface* Weld = B.Mat(FLinearColor(0.10f, 0.085f, 0.07f), 0.6f, 0.6f);
			for (const float S : { -1.f, 1.f })
			{
				struct FPlate { float X0, X1, Z0, Z1, Roll; };
				const FPlate Plates[2] = { { 3.f, 11.5f, -2.5f, 1.4f, 4.f }, { 12.5f, 19.f, -1.2f, 2.6f, -3.f } };
				for (const FPlate& Pl : Plates)
				{
					const float Y = 3.75f * S;
					B.Box(Plate, FVector(Pl.X0, Y - 0.25f, Pl.Z0), FVector(Pl.X1, Y + 0.25f, Pl.Z1), FRotator(0.f, 0.f, Pl.Roll));
					// Weld beads along the top and bottom edge, rivets in the corners.
					for (float X = Pl.X0 + 0.4f; X < Pl.X1; X += 0.9f)
					{
						B.Part(EShape::Sphere, Weld, FVector(X, Y, Pl.Z1 + 0.1f), FVector(0.85f, 0.75f, 0.55f));
						B.Part(EShape::Sphere, Weld, FVector(X, Y, Pl.Z0 - 0.1f), FVector(0.85f, 0.75f, 0.55f));
					}
					for (const FVector2D C : { FVector2D(Pl.X0 + 0.8f, Pl.Z0 + 0.7f), FVector2D(Pl.X1 - 0.8f, Pl.Z0 + 0.7f), FVector2D(Pl.X0 + 0.8f, Pl.Z1 - 0.7f), FVector2D(Pl.X1 - 0.8f, Pl.Z1 - 0.7f) })
					{
						B.Part(EShape::Sphere, Weld, FVector(C.X, Y + 0.3f * S, C.Y), FVector(0.7f));
					}
				}
			}
			B.Collar(Plate, 33.f, 2.4f, 9.8f);
			B.Collar(Weld, 31.7f, 0.5f, 10.f);
			B.Collar(Weld, 34.3f, 0.5f, 10.f);
			break;
		}
		case 2: // Legion: a golden laurel wreath on each side
		{
			UMaterialInterface* Gold = B.Mat(GoldColor, 0.22f, 1.f);
			for (const float S : { -1.f, 1.f })
			{
				const FVector Centre(10.5f, 3.8f * S, -0.3f);
				for (int32 Branch = 0; Branch < 2; ++Branch)
				{
					for (int32 I = 0; I < 7; ++I)
					{
						// Two branches from the bottom up both sides, open at the top.
						const float Deg = Branch == 0 ? (-100.f + I * 25.f) : (-80.f - I * 25.f);
						const float Rad = FMath::DegreesToRadians(Deg);
						const float R = 3.0f + ((I % 2) ? 0.45f : -0.3f);
						const FVector Where = Centre + FVector(FMath::Cos(Rad) * R, 0.f, FMath::Sin(Rad) * R);
						const float Tangent = FMath::RadiansToDegrees(FMath::Atan2(FMath::Cos(Rad), -FMath::Sin(Rad))) * (Branch == 0 ? 1.f : -1.f);
						B.Part(EShape::Sphere, Gold, Where, FVector(1.7f, 0.35f, 0.7f), FRotator(Tangent + ((I % 2) ? 28.f : -28.f), 0.f, 0.f));
					}
				}
				B.Part(EShape::Sphere, Gold, Centre + FVector(0.f, 0.f, -3.2f), FVector(0.9f, 0.45f, 0.9f));
			}
			B.Collar(Gold, 32.f, 0.8f, 9.9f);
			B.Collar(Gold, 40.f, 0.8f, 9.9f);
			break;
		}
		case 3: // Syndicate: neon strips
		{
			UMaterialInterface* Pink = B.Mat(FLinearColor(1.f, 0.05f, 0.6f), 0.3f, 0.f, 6.f);
			UMaterialInterface* Cyan = B.Mat(FLinearColor(0.05f, 0.85f, 1.f), 0.3f, 0.f, 6.f);
			for (const float S : { -1.f, 1.f })
			{
				B.Box(Pink, FVector(1.f, 3.55f * S - 0.15f, 2.75f), FVector(19.5f, 3.55f * S + 0.15f, 3.05f));
				B.Box(Cyan, FVector(1.f, 3.55f * S - 0.15f, -3.05f), FVector(19.5f, 3.55f * S + 0.15f, -2.75f));
				B.Box(Pink, FVector(29.f, 4.5f * S - 0.15f, BarrelZ - 0.15f), FVector(45.f, 4.5f * S + 0.15f, BarrelZ + 0.15f));
				B.Box(Cyan, FVector(15.5f, 2.7f * S - 0.12f, -12.9f), FVector(25.5f, 2.7f * S + 0.12f, -12.6f));
			}
			B.Box(Cyan, FVector(-6.f, -0.2f, 5.3f), FVector(-0.5f, 0.2f, 5.6f));
			break;
		}
		case 4: // Void Corps: pressure rings, a gauge and hoses
		{
			UMaterialInterface* White = B.Mat(FLinearColor(0.78f, 0.8f, 0.83f), 0.45f, 0.05f);
			UMaterialInterface* Seam = B.Mat(FLinearColor(0.05f, 0.055f, 0.06f), 0.5f, 0.4f);
			for (const float X : { 32.f, 40.f })
			{
				B.Collar(White, X, 1.6f, 10.4f);
				B.Collar(Seam, X - 0.95f, 0.3f, 10.6f);
				B.Collar(Seam, X + 0.95f, 0.3f, 10.6f);
			}
			// The gauge on the left side, facing out.
			B.Part(EShape::Cylinder, White, FVector(8.f, -3.95f, 0.f), FVector(4.6f, 4.6f, 0.7f), FRotator(0.f, 0.f, 90.f));
			B.Part(EShape::Cylinder, B.Mat(FLinearColor(0.01f, 0.012f, 0.016f), 0.08f, 0.f), FVector(8.f, -4.35f, 0.f), FVector(3.6f, 3.6f, 0.15f), FRotator(0.f, 0.f, 90.f));
			B.Box(B.Mat(FLinearColor(1.f, 0.1f, 0.05f), 0.4f, 0.f, 2.f), FVector(7.9f, -4.5f, -0.1f), FVector(9.4f, -4.4f, 0.1f), FRotator(35.f, 0.f, 0.f));
			for (const float S : { -1.f, 1.f })
			{
				B.Rod(Seam, FVector(20.f, 3.3f * S, -3.6f), FVector(29.f, 4.2f * S, -2.2f), 0.9f);
			}
			break;
		}
		case 5: // Hollow Court: curved horns at the back and over the muzzle
		{
			UMaterialInterface* Bone = B.Mat(FLinearColor(0.72f, 0.65f, 0.52f), 0.55f, 0.f);
			UMaterialInterface* Dark = B.Mat(FLinearColor(0.02f, 0.018f, 0.02f), 0.5f, 0.3f);
			auto Horn = [&B, Bone](const FVector& Start, const FVector& Dir1, const FVector& Dir2, float Size)
			{
				const FVector A = Start;
				const FVector Bp = A + Dir1 * 2.2f * Size;
				const FVector C = Bp + (Dir1 + Dir2).GetSafeNormal() * 2.0f * Size;
				const FVector D = C + Dir2 * 2.4f * Size;
				B.Rod(Bone, A, Bp, 1.5f * Size);
				B.Rod(Bone, Bp - Dir1 * 0.2f, C, 1.15f * Size);
				B.Rod(Bone, C - (Dir1 + Dir2).GetSafeNormal() * 0.2f, D, 0.9f * Size, EShape::Cone);
			};
			for (const float S : { -1.f, 1.f })
			{
				Horn(FVector(-6.f, 2.2f * S, 4.2f), FVector(-0.4f, 0.5f * S, 0.75f).GetSafeNormal(), FVector(-0.9f, 0.25f * S, 0.1f).GetSafeNormal(), 1.f);
				Horn(FVector(57.f, 2.4f * S, 3.2f), FVector(0.2f, 0.45f * S, 0.85f).GetSafeNormal(), FVector(0.9f, 0.2f * S, 0.3f).GetSafeNormal(), 0.6f);
			}
			B.Collar(Dark, 33.f, 1.f, 9.9f);
			B.Part(EShape::Sphere, B.Mat(FLinearColor(0.6f, 0.1f, 1.f), 0.3f, 0.f, 4.f), FVector(-6.f, 0.f, 5.9f), FVector(1.2f));
			break;
		}
		case 6: // Obsidian: gold edges
		{
			UMaterialInterface* Gold = B.Mat(GoldColor, 0.22f, 1.f);
			for (const float S : { -1.f, 1.f })
			{
				B.Box(Gold, FVector(-6.f, 3.05f * S - 0.18f, 3.85f), FVector(26.f, 3.05f * S + 0.18f, 4.2f));
				B.Box(Gold, FVector(-6.f, 3.05f * S - 0.18f, -4.4f), FVector(26.f, 3.05f * S + 0.18f, -4.05f));
			}
			B.Collar(Gold, 45.f, 0.5f, 9.4f);
			B.Collar(B.Mat(FLinearColor(1.f, 0.05f, 0.02f), 0.3f, 0.f, 5.f), 29.6f, 0.4f, 9.0f);
			break;
		}
		default:
			break;
		}
	}

	void AddKillCounter(FPartBuilder& B, const FIACosmeticLoadout& L, const FPalette& P)
	{
		if (!L.bKillCounter)
		{
			return;
		}
		UMaterialInterface* Housing = B.Mat(P.Trim);
		UMaterialInterface* Screen = B.Mat(FLinearColor(0.008f, 0.01f, 0.012f), 0.15f, 0.f);
		UMaterialInterface* Lit = B.Mat(P.Core, 0.3f, 0.f, 5.f);
		UMaterialInterface* Unlit = B.Mat(P.Core * 0.08f, 0.4f, 0.f);

		// A small display on the back left of the receiver, turned towards the eye of the player (first person) and readable from the side.
		const FTransform Panel(FRotator(16.f, -150.f, 0.f), FVector(-4.2f, -5.2f, 1.6f));
		B.Box(Housing, FVector(-5.f, -4.9f, 0.2f), FVector(-2.f, -3.1f, 2.8f));
		B.PartIn(Panel, EShape::Cube, Housing, FVector(0.f, 0.f, 0.f), FVector(1.f, 8.2f, 3.8f));
		B.PartIn(Panel, EShape::Cube, Screen, FVector(0.52f, 0.f, 0.f), FVector(0.06f, 7.4f, 3.0f));

		const FString Digits = FString::FromInt(FMath::Clamp(L.KillCounterValue, 0, 9999999));
		const int32 Count = Digits.Len();
		const float Cell = FMath::Min(1.3f, 7.0f / Count);   // width of one digit cell
		const float W = Cell * 0.62f;                        // digit width
		const float H = 2.2f;                                // digit height
		const float T = FMath::Max(0.16f, Cell * 0.14f);     // segment thickness
		for (int32 I = 0; I < Count; ++I)
		{
			const int32 Value = Digits[I] - TEXT('0');
			// Left to right as the viewer sees it, who looks along the panel's -X: that is the panel's -Y.
			const float Y = (Count * 0.5f - I - 0.5f) * Cell;
			const float X = 0.58f;
			const FVector Segs[7][2] = {
				{ FVector(X, Y, H * 0.5f),             FVector(0.05f, W, T) },          // a
				{ FVector(X, Y - W * 0.5f, H * 0.25f), FVector(0.05f, T, H * 0.5f) },   // b (viewer's right = -Y)
				{ FVector(X, Y - W * 0.5f, -H * 0.25f), FVector(0.05f, T, H * 0.5f) },  // c
				{ FVector(X, Y, -H * 0.5f),            FVector(0.05f, W, T) },          // d
				{ FVector(X, Y + W * 0.5f, -H * 0.25f), FVector(0.05f, T, H * 0.5f) },  // e
				{ FVector(X, Y + W * 0.5f, H * 0.25f), FVector(0.05f, T, H * 0.5f) },   // f
				{ FVector(X, Y, 0.f),                  FVector(0.05f, W, T) },          // g
			};
			for (int32 S = 0; S < 7; ++S)
			{
				const bool bOn = (DigitSegments[Value] >> S) & 1;
				B.PartIn(Panel, EShape::Cube, bOn ? Lit : Unlit, Segs[S][0], Segs[S][1]);
			}
		}

		// A ring of ten ticks around the handguard: one lit tick per thousand kills.
		const int32 Thousands = FMath::Clamp(L.KillCounterValue / 1000, 0, 10);
		for (int32 I = 0; I < 10; ++I)
		{
			const float Rad = FMath::DegreesToRadians(90.f + I * 36.f);
			const FVector Where(27.5f, FMath::Cos(Rad) * 4.95f, BarrelZ + FMath::Sin(Rad) * 4.95f);
			B.Part(EShape::Cube, I < Thousands ? Lit : Unlit, Where, FVector(1.4f, 0.7f, 0.5f), FRotator(0.f, 0.f, I * 36.f));
		}
	}
}

namespace IARifleLook
{
	FLinearColor CoreColor(const FIACosmeticLoadout& Loadout, const FLinearColor& Accent)
	{
		return MakePalette(Loadout, Accent).Core;
	}

	void StyleSlot(UMaterialInstanceDynamic* Material, int32 Slot, const FIACosmeticLoadout& Loadout, const FLinearColor& Accent)
	{
		if (!Material)
		{
			return;
		}
		const FPalette P = MakePalette(Loadout, Accent);
		auto Surface = [Material](const FSlotLook& Look)
		{
			Material->SetVectorParameterValue(TEXT("BodyColor"), Look.Color);
			Material->SetScalarParameterValue(TEXT("Roughness"), Look.Roughness);
			Material->SetScalarParameterValue(TEXT("Metallic"), Look.Metallic);
		};
		switch (Slot)
		{
		case SlotBody:
			Surface(P.Body);
			Material->SetScalarParameterValue(TEXT("Detail"), P.Detail);
			break;
		case SlotTrim:
			Surface(P.Trim);
			Material->SetScalarParameterValue(TEXT("Detail"), P.Detail);
			break;
		case SlotAccent:
			Surface(P.Paint);
			break;
		case SlotCore:
			// The only light source of the rifle: emissive in the core colour (Glow is animated by the character).
			Material->SetVectorParameterValue(TEXT("BodyColor"), P.Core * 0.12f);
			Material->SetVectorParameterValue(TEXT("AccentColor"), P.Core);
			break;
		default:
			break;
		}
	}

	void AddParts(AActor* Owner, USceneComponent* Root, bool bFirstPerson, const FIACosmeticLoadout& Loadout,
		const FLinearColor& Accent, UMaterialInterface* WeaponMaterial, TArray<TObjectPtr<UStaticMeshComponent>>& OutParts)
	{
		if (!Owner || !Root || !WeaponMaterial)
		{
			return;
		}
		const FPalette P = MakePalette(Loadout, Accent);
		FPartBuilder Builder(Owner, Root, bFirstPerson, WeaponMaterial, OutParts);
		AddLivery(Builder, Loadout, P);
		AddBarrel(Builder, Loadout, P);
		AddStock(Builder, Loadout, P);
		AddFins(Builder, Loadout, P);
		AddCharm(Builder, Loadout, P);
		AddKillCounter(Builder, Loadout, P);
	}

	FLinearColor BeamColor(const FIACosmeticLoadout& Loadout, const FLinearColor& Default, bool bTeamGame)
	{
		// In team games the beam keeps the team colour: who shot must stay readable. The style still applies.
		if (bTeamGame || !Loadout.bCustomBeamColor)
		{
			return Default;
		}
		return FLinearColor::FromSRGBColor(Loadout.BeamColor);
	}
}
