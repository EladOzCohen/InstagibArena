// Instagib Arena

#pragma once

#include "CoreMinimal.h"

/** Shapes available for accessories (the engine's basic shapes, each 100 cm). */
enum class EIAShape : uint8
{
	Cube,
	Cylinder,
	Sphere,
	Cone
};

/** Which color an accessory takes. */
enum class EIAPartColor : uint8
{
	Body,
	Accent,
	Team,  // the team color in team games, the accent color otherwise
	Glow,  // the accent color, emissive
	Light  // off-white, for eyes, spots and fur
};

/**
 * One piece attached to a bone. Offset, rotation and size are written in character space
 * (X forward, Y right, Z up, centimeters) relative to the bone's position,
 * so they do not depend on how the mannequin's bones are oriented.
 */
struct FIAAccessory
{
	EIAShape Shape;
	const TCHAR* Bone;
	FVector Offset;
	FRotator Rotation;
	FVector Size;
	EIAPartColor Color;
};

/** The look of one character: which mannequin, how it is scaled, colors and accessories. */
struct FIACharacterLook
{
	const TCHAR* Name;
	const TCHAR* Title;
	bool bQuinn;                 // false = Manny, true = Quinn
	float MeshScale;             // uniform, so that attached parts are not skewed
	FLinearColor Body;
	FLinearColor Accent;
	float Roughness;
	float Metallic;
	TArray<FIAAccessory> Parts;
	float BodyGlow = 0.f;        // makes the whole body emissive (used by the hologram)
	float AccentMetal = 0.f;     // 1 = the accent parts are metal (gold, steel); everything else on a character is matte
};

namespace IACharacters
{
	/** Number of distinct looks. Roster entries beyond this reuse them with a shifted hue. */
	inline constexpr int32 LookCount = 15;

	/** Rotation that turns a cylinder's long axis (Z) into the character's forward axis (X). */
	inline const FRotator AlongX(-90.f, 0.f, 0.f);

	inline const FIACharacterLook& GetLook(int32 Index)
	{
		static const TArray<FIACharacterLook> Looks = {
			// 0 - Bulwark: wide, heavy armor with huge shoulders.
			{ TEXT("Bulwark"), TEXT("Heavy"), false, 1.12f,
			  FLinearColor(0.10f, 0.11f, 0.14f), FLinearColor(1.0f, 0.38f, 0.02f), 0.6f, 0.35f,
			  {
				{ EIAShape::Sphere,   TEXT("upperarm_l"), FVector(0, -6, 6),  FRotator(0, 0, 0), FVector(30, 34, 26), EIAPartColor::Team },
				{ EIAShape::Sphere,   TEXT("upperarm_r"), FVector(0, 6, 6),   FRotator(0, 0, 0), FVector(30, 34, 26), EIAPartColor::Team },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(14, 0, 0),  FRotator(0, 0, 0), FVector(8, 38, 30),  EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 0, 6),  FRotator(0, 0, 0), FVector(7, 20, 6),   EIAPartColor::Glow },
				{ EIAShape::Cylinder, TEXT("head"),       FVector(0, 0, 14),  FRotator(0, 0, 0), FVector(26, 26, 5),  EIAPartColor::Body },
			  } },
			// 1 - Vesper: slim, tall, with antenna and a glowing visor.
			{ TEXT("Vesper"), TEXT("Assassin"), true, 1.0f,
			  FLinearColor(0.30f, 0.04f, 0.60f), FLinearColor(0.0f, 0.9f, 1.0f), 0.8f, 0.0f,
			  {
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 0, 4),  FRotator(0, 0, 0), FVector(6, 20, 5),   EIAPartColor::Glow },
				{ EIAShape::Cylinder, TEXT("head"),       FVector(-4, 8, 28), FRotator(0, 0, -18), FVector(1.5f, 1.5f, 38), EIAPartColor::Team },
				{ EIAShape::Cone,     TEXT("lowerarm_l"), FVector(14, 0, -2), FRotator(-90, 0, 0), FVector(7, 7, 40), EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("lowerarm_r"), FVector(14, 0, -2), FRotator(-90, 0, 0), FVector(7, 7, 40), EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(10, 0, 4),  FRotator(0, 0, 0), FVector(4, 18, 4),   EIAPartColor::Team },
			  } },
			// 2 - Khet: golden headdress, collar and arm bands.
			{ TEXT("Khet"), TEXT("Pharaoh"), false, 1.0f,
			  FLinearColor(0.02f, 0.40f, 0.36f), FLinearColor(1.0f, 0.62f, 0.05f), 0.85f, 0.0f,
			  {
				{ EIAShape::Cone,     TEXT("head"),       FVector(-2, 0, 24), FRotator(0, 0, 0), FVector(20, 20, 38), EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("head"),       FVector(-4, 0, 6),  FRotator(0, 0, 0), FVector(26, 30, 5),  EIAPartColor::Team },
				{ EIAShape::Cylinder, TEXT("spine_05"),   FVector(2, 0, 10),  FRotator(0, 0, 0), FVector(44, 44, 5),  EIAPartColor::Accent },
				{ EIAShape::Cylinder, TEXT("upperarm_l"), FVector(0, -4, 0),  FRotator(0, 0, 90), FVector(13, 13, 5),  EIAPartColor::Accent },
				{ EIAShape::Cylinder, TEXT("upperarm_r"), FVector(0, 4, 0),   FRotator(0, 0, 90), FVector(13, 13, 5),  EIAPartColor::Accent },
			  }, 0.f, 0.9f },
			// 3 - Razorclaw: green alien with back spikes, head crest and claws.
			{ TEXT("Razorclaw"), TEXT("Hunter"), true, 1.04f,
			  FLinearColor(0.16f, 0.60f, 0.04f), FLinearColor(0.9f, 0.05f, 0.05f), 0.7f, 0.0f,
			  {
				{ EIAShape::Cone,     TEXT("spine_04"),   FVector(-12, 0, 14), FRotator(40, 0, 0),  FVector(10, 10, 30), EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("spine_05"),   FVector(-12, 0, 16), FRotator(25, 0, 0),  FVector(12, 12, 36), EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("head"),       FVector(-6, 0, 18),  FRotator(35, 0, 0),  FVector(8, 8, 28),   EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("hand_l"),     FVector(10, 0, 0),   FRotator(-90, 0, 0), FVector(6, 6, 22),   EIAPartColor::Glow },
				{ EIAShape::Cone,     TEXT("hand_r"),     FVector(10, 0, 0),   FRotator(-90, 0, 0), FVector(6, 6, 22),   EIAPartColor::Glow },
			  } },
			// 4 - Cinder: black robot with a glowing core, one eye and exhaust vents.
			{ TEXT("Cinder"), TEXT("Furnace"), false, 1.0f,
			  FLinearColor(0.025f, 0.025f, 0.03f), FLinearColor(1.0f, 0.35f, 0.0f), 0.5f, 0.8f,
			  {
				{ EIAShape::Sphere,   TEXT("spine_05"),   FVector(14, 0, -2),  FRotator(0, 0, 0), FVector(17, 17, 17), EIAPartColor::Glow },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(10, 0, 5),   FRotator(0, 0, 0), FVector(8, 8, 8),    EIAPartColor::Glow },
				{ EIAShape::Cylinder, TEXT("spine_04"),   FVector(-12, -9, 6), FRotator(0, 0, 0), FVector(7, 7, 34),   EIAPartColor::Team },
				{ EIAShape::Cylinder, TEXT("spine_04"),   FVector(-12, 9, 6),  FRotator(0, 0, 0), FVector(7, 7, 34),   EIAPartColor::Team },
				{ EIAShape::Cube,     TEXT("pelvis"),     FVector(10, 0, 4),   FRotator(0, 0, 0), FVector(3, 24, 6),   EIAPartColor::Accent },
			  } },
			// 5 - Marlowe: field soldier with a helmet, a team-colored vest and a backpack.
			{ TEXT("Marlowe"), TEXT("Soldier"), false, 1.0f,
			  FLinearColor(0.14f, 0.18f, 0.07f), FLinearColor(0.9f, 0.75f, 0.2f), 0.9f, 0.0f,
			  {
				{ EIAShape::Sphere,   TEXT("head"),       FVector(0, 0, 9),     FRotator(0, 0, 0), FVector(27, 25, 22), EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 0, 5),    FRotator(0, 0, 0), FVector(5, 22, 4),   EIAPartColor::Glow },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(13, 0, -1),   FRotator(0, 0, 0), FVector(8, 34, 28),  EIAPartColor::Team },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-14, 0, 6),   FRotator(0, 0, 0), FVector(14, 26, 32), EIAPartColor::Body },
			  } },
			// 6 - Nyx: a shadow with glowing eyes, small horns and a long cape.
			{ TEXT("Nyx"), TEXT("Shade"), false, 1.02f,
			  FLinearColor(0.02f, 0.0f, 0.05f), FLinearColor(0.75f, 0.1f, 1.0f), 0.9f, 0.0f,
			  {
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 4.5f, 5),  FRotator(0, 0, 0),   FVector(3, 5, 2),    EIAPartColor::Glow },
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, -4.5f, 5), FRotator(0, 0, 0),   FVector(3, 5, 2),    EIAPartColor::Glow },
				{ EIAShape::Cone,     TEXT("head"),       FVector(-2, 8, 15),    FRotator(0, 0, -25), FVector(5, 5, 18),   EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("head"),       FVector(-2, -8, 15),   FRotator(0, 0, 25),  FVector(5, 5, 18),   EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(-9, 0, -24),   FRotator(-6, 0, 0),  FVector(3, 34, 66),  EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(-10.5f, 0, 6), FRotator(0, 0, 0),   FVector(2, 36, 3),   EIAPartColor::Team },
			  } },
			// 7 - Oddjob: a jester with a red nose, two-pointed hat and a ruff.
			{ TEXT("Oddjob"), TEXT("Jester"), true, 1.0f,
			  FLinearColor(0.88f, 0.88f, 0.92f), FLinearColor(1.0f, 0.05f, 0.12f), 0.85f, 0.0f,
			  {
				{ EIAShape::Sphere,   TEXT("head"),       FVector(12, 0, -1),  FRotator(0, 0, 0),   FVector(8, 8, 8),    EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("head"),       FVector(0, 9, 18),   FRotator(0, 0, -35), FVector(10, 10, 34), EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("head"),       FVector(0, -9, 18),  FRotator(0, 0, 35),  FVector(10, 10, 34), EIAPartColor::Team },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(0, 19, 33),  FRotator(0, 0, 0),   FVector(8, 8, 8),    EIAPartColor::Light },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(0, -19, 33), FRotator(0, 0, 0),   FVector(8, 8, 8),    EIAPartColor::Glow },
				{ EIAShape::Cylinder, TEXT("spine_05"),   FVector(3, 0, 11),   FRotator(0, 0, 0),   FVector(46, 46, 7),  EIAPartColor::Light },
			  } },
			// 8 - Sable: a ninja with a headband, a scarf and two crossed blades on the back.
			{ TEXT("Sable"), TEXT("Ninja"), true, 1.0f,
			  FLinearColor(0.03f, 0.04f, 0.09f), FLinearColor(0.95f, 0.05f, 0.18f), 0.85f, 0.0f,
			  {
				{ EIAShape::Cube,     TEXT("head"),       FVector(0, 0, 8),      FRotator(0, 0, 0),   FVector(25, 27, 4.5f), EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("head"),       FVector(-15, 0, 4),    FRotator(-18, 0, 0), FVector(24, 4, 5),    EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 0, 5),     FRotator(0, 0, 0),   FVector(3, 22, 3),    EIAPartColor::Glow },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-14, 0, 10),   FRotator(0, 0, 38),  FVector(4, 4, 64),    EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-14, 0, 10),   FRotator(0, 0, -38), FVector(4, 4, 64),    EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-14, 0, -2),   FRotator(0, 0, 0),   FVector(5, 14, 3),    EIAPartColor::Accent },
			  } },
			// 9 - Gearhead: a mechanic in orange overalls with goggles, a tool belt, a wrench and a gear.
			{ TEXT("Gearhead"), TEXT("Mechanic"), false, 1.04f,
			  FLinearColor(0.78f, 0.28f, 0.03f), FLinearColor(0.55f, 0.6f, 0.65f), 0.85f, 0.0f,
			  {
				{ EIAShape::Cylinder, TEXT("head"),       FVector(9, 5, 6),      IACharacters::AlongX, FVector(8, 8, 5),   EIAPartColor::Accent },
				{ EIAShape::Cylinder, TEXT("head"),       FVector(9, -5, 6),     IACharacters::AlongX, FVector(8, 8, 5),   EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("head"),       FVector(6, 0, 6),      FRotator(0, 0, 0),    FVector(3, 20, 3),  EIAPartColor::Team },
				{ EIAShape::Cylinder, TEXT("pelvis"),     FVector(0, 0, 3),      FRotator(0, 0, 0),    FVector(38, 38, 8), EIAPartColor::Team },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-13, 11, -4),  FRotator(0, 0, 0),    FVector(3, 3, 52),  EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-13, 11, 24),  FRotator(0, 0, 0),    FVector(4, 12, 5),  EIAPartColor::Accent },
				{ EIAShape::Cylinder, TEXT("upperarm_r"), FVector(0, 6, 8),      FRotator(0, 0, 90),   FVector(14, 14, 4), EIAPartColor::Glow },
			  }, 0.f, 0.9f },
			// 10 - Aurelia: a gladiator in gold with a crested helmet and a red skirt.
			{ TEXT("Aurelia"), TEXT("Gladiator"), true, 1.0f,
			  FLinearColor(0.62f, 0.43f, 0.05f), FLinearColor(0.8f, 0.04f, 0.04f), 0.5f, 0.85f,
			  {
				{ EIAShape::Sphere,   TEXT("head"),       FVector(0, 0, 9),    FRotator(0, 0, 0), FVector(27, 25, 22), EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("head"),       FVector(-2, 0, 20),  FRotator(0, 0, 0), FVector(32, 3.5f, 15), EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("upperarm_l"), FVector(0, -6, 8),   FRotator(0, 0, 0), FVector(14, 22, 6),  EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("upperarm_r"), FVector(0, 6, 8),    FRotator(0, 0, 0), FVector(14, 22, 6),  EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(14, 0, -1),  FRotator(0, 0, 0), FVector(6, 30, 28),  EIAPartColor::Accent },
				{ EIAShape::Cylinder, TEXT("pelvis"),     FVector(0, 0, -5),   FRotator(0, 0, 0), FVector(40, 40, 14), EIAPartColor::Team },
			  } },
			// 11 - Tundra: an arctic fighter in white fur with ice crystals on the shoulders and back.
			{ TEXT("Tundra"), TEXT("Arctic"), false, 1.06f,
			  FLinearColor(0.72f, 0.86f, 1.0f), FLinearColor(0.1f, 0.6f, 1.0f), 0.95f, 0.0f,
			  {
				{ EIAShape::Cylinder, TEXT("spine_05"),   FVector(2, 0, 9),     FRotator(0, 0, 0),   FVector(48, 48, 12), EIAPartColor::Light },
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 0, 3),    FRotator(0, 0, 0),   FVector(4, 22, 12),  EIAPartColor::Glow },
				{ EIAShape::Cone,     TEXT("upperarm_l"), FVector(0, -8, 16),   FRotator(0, 0, 20),  FVector(8, 8, 26),   EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("upperarm_r"), FVector(0, 8, 16),    FRotator(0, 0, -20), FVector(8, 8, 26),   EIAPartColor::Accent },
				{ EIAShape::Cone,     TEXT("spine_04"),   FVector(-14, -6, 10), FRotator(20, 0, 0), FVector(9, 9, 34),   EIAPartColor::Glow },
				{ EIAShape::Cone,     TEXT("spine_04"),   FVector(-14, 6, 10),  FRotator(20, 0, 0), FVector(9, 9, 30),   EIAPartColor::Team },
			  } },
			// 12 - Mosscap: a mushroom creature with a huge spotted cap and shelf fungi on its back.
			{ TEXT("Mosscap"), TEXT("Fungus"), false, 0.98f,
			  FLinearColor(0.38f, 0.24f, 0.12f), FLinearColor(0.9f, 0.12f, 0.1f), 0.85f, 0.0f,
			  {
				{ EIAShape::Sphere,   TEXT("head"),       FVector(0, 0, 20),    FRotator(0, 0, 0), FVector(64, 64, 28), EIAPartColor::Accent },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(8, 10, 31),   FRotator(0, 0, 0), FVector(10, 10, 4),  EIAPartColor::Light },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(-10, -12, 30),FRotator(0, 0, 0), FVector(10, 10, 4),  EIAPartColor::Light },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(14, -8, 30),  FRotator(0, 0, 0), FVector(8, 8, 4),    EIAPartColor::Light },
				{ EIAShape::Sphere,   TEXT("head"),       FVector(-12, 14, 29), FRotator(0, 0, 0), FVector(8, 8, 4),    EIAPartColor::Light },
				{ EIAShape::Cylinder, TEXT("spine_04"),   FVector(-11, 0, 6),   IACharacters::AlongX, FVector(24, 24, 5), EIAPartColor::Accent },
				{ EIAShape::Cylinder, TEXT("spine_04"),   FVector(-11, 0, -8),  IACharacters::AlongX, FVector(18, 18, 4), EIAPartColor::Team },
			  } },
			// 13 - Specter-9: a glowing hologram with a halo and floating cubes.
			{ TEXT("Specter-9"), TEXT("Hologram"), false, 1.0f,
			  FLinearColor(0.0f, 0.40f, 0.55f), FLinearColor(0.7f, 1.0f, 1.0f), 0.55f, 0.0f,
			  {
				{ EIAShape::Cylinder, TEXT("head"),       FVector(0, 0, 34),    FRotator(0, 0, 0), FVector(36, 36, 1.6f), EIAPartColor::Glow },
				{ EIAShape::Cube,     TEXT("head"),       FVector(10, 0, 4),    FRotator(0, 0, 0), FVector(3, 22, 4),     EIAPartColor::Light },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(6, -22, 0),   FRotator(15, 20, 10), FVector(6, 6, 6),   EIAPartColor::Glow },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(6, 22, 0),    FRotator(40, 10, 5),  FVector(6, 6, 6),   EIAPartColor::Glow },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(-8, -22, 10), FRotator(25, 45, 0),  FVector(5, 5, 5),   EIAPartColor::Team },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(-8, 22, 10),  FRotator(10, 60, 30), FVector(5, 5, 5),   EIAPartColor::Team },
			  }, 0.8f },
			// 14 - Brimstone: a demon with horns, wings, a tail and a glowing crack in the chest.
			{ TEXT("Brimstone"), TEXT("Demon"), true, 1.06f,
			  FLinearColor(0.30f, 0.02f, 0.01f), FLinearColor(1.0f, 0.45f, 0.0f), 0.65f, 0.0f,
			  {
				{ EIAShape::Cone,     TEXT("head"),       FVector(0, 8, 16),    FRotator(0, 0, -25), FVector(7, 7, 32),   EIAPartColor::Body },
				{ EIAShape::Cone,     TEXT("head"),       FVector(0, -8, 16),   FRotator(0, 0, 25),  FVector(7, 7, 32),   EIAPartColor::Body },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-16, 26, 14), FRotator(0, 0, -30), FVector(3, 50, 34),  EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("spine_04"),   FVector(-16, -26, 14),FRotator(0, 0, 30),  FVector(3, 50, 34),  EIAPartColor::Accent },
				{ EIAShape::Cube,     TEXT("spine_05"),   FVector(13, 0, 2),    FRotator(0, 0, 0),   FVector(3, 10, 22),  EIAPartColor::Glow },
				{ EIAShape::Cone,     TEXT("pelvis"),     FVector(-14, 0, -8),  FRotator(100, 0, 0), FVector(6, 6, 50),   EIAPartColor::Body },
			  } },
		};
		return Looks[Index % Looks.Num()];
	}
}
