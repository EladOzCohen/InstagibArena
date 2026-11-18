// Instagib Arena

#include "IACharacterVariants.h"

namespace
{
	/** Scales saturation and value of a linear colour (HSV in linear space, like the roster's hue turn). */
	FLinearColor Shade(const FLinearColor& C, float Saturation, float Value)
	{
		FLinearColor Hsv = C.LinearRGBToHSV();
		Hsv.G = FMath::Clamp(Hsv.G * Saturation, 0.f, 1.f);
		Hsv.B = FMath::Max(0.f, Hsv.B * Value);
		FLinearColor Out = Hsv.HSVToLinearRGB();
		Out.A = C.A;
		return Out;
	}

	const FLinearColor Gold(1.0f, 0.62f, 0.16f);
}

namespace IACharacterVariants
{
	FIACharacterLook Apply(const FIACharacterLook& Base, uint8 Variant, FLinearColor& OutGlow)
	{
		FIACharacterLook Look = Base;
		OutGlow = Base.Accent;
		switch (Variant)
		{
		case Veteran:
		{
			// A suit that has seen many seasons: darker, greyer, rougher and less shiny. The accent stays, so the character is still known.
			Look.Body = Shade(Base.Body, 0.55f, 0.72f);
			Look.Roughness = FMath::Clamp(Base.Roughness + 0.18f, 0.f, 0.95f);
			Look.Metallic = Base.Metallic * 0.75f;
			if (Base.GearCloth.A > 0.f)
			{
				Look.GearCloth = Shade(Base.GearCloth, 0.5f, 0.7f);
				Look.GearCloth.A = 1.f;
			}
			else
			{
				Look.GearCloth = FLinearColor(Look.Body.R * 0.55f, Look.Body.G * 0.52f, Look.Body.B * 0.48f, 1.f);   // a little brown: dust
			}
			Look.Accent = Shade(Base.Accent, 0.85f, 0.9f);
			OutGlow = Base.Accent;
			break;
		}
		case Elite:
		{
			// Gold trim: the accent becomes polished gold, the suit gains metal and a deeper, richer colour.
			Look.Body = Shade(Base.Body, 1.1f, 0.85f);
			Look.Accent = Gold;
			Look.AccentMetal = 1.f;
			Look.Metallic = FMath::Max(Base.Metallic, 0.6f);
			Look.Roughness = FMath::Clamp(Base.Roughness - 0.12f, 0.25f, 0.9f);
			OutGlow = Base.Accent;
			break;
		}
		case Obsidian:
		{
			// Volcanic glass: near black, glossy, gold trim and a red glow in the visors.
			Look.Body = FLinearColor(0.012f, 0.012f, 0.016f);
			Look.Accent = Gold;
			Look.AccentMetal = 1.f;
			Look.Metallic = 0.75f;
			Look.Roughness = 0.3f;
			Look.GearCloth = FLinearColor(0.02f, 0.018f, 0.022f, 1.f);
			OutGlow = FLinearColor(1.f, 0.05f, 0.02f);
			break;
		}
		default:
			break;
		}
		return Look;
	}
}
