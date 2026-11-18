// Instagib Arena

#include "IACosmetics.h"

namespace
{
	FString Hex(const FColor& C)
	{
		return FString::Printf(TEXT("%02X%02X%02X%02X"), C.R, C.G, C.B, C.A);
	}

	FColor ParseColor(const FString& S, const FColor& Default)
	{
		if (S.Len() != 8)
		{
			return Default;
		}
		const uint32 V = FParse::HexNumber(*S);
		return FColor((V >> 24) & 255, (V >> 16) & 255, (V >> 8) & 255, V & 255);
	}
}

FString FIACosmeticLoadout::ToString() const
{
	return FString::Printf(TEXT("bc=%d,bcol=%s,bs=%d,cr=%d,rb=%s,ra=%s,rc=%s,rf=%d,ba=%d,st=%d,fi=%d,ch=%d,rl=%d,kc=%d,ke=%d,cv=%d,rk=%d,ti=%d"),
		bCustomBeamColor ? 1 : 0, *Hex(BeamColor), BeamStyle, bCustomRifle ? 1 : 0, *Hex(RifleBody), *Hex(RifleAccent), *Hex(RifleCore),
		RifleFinish, Barrel, Stock, Fins, Charm, RifleLivery, bKillCounter ? 1 : 0, KillEffect, CharacterVariant, Rank, TitleId);
}

void FIACosmeticLoadout::FromString(const FString& Text)
{
	*this = FIACosmeticLoadout();
	TArray<FString> Pairs;
	Text.ParseIntoArray(Pairs, TEXT(","));
	for (const FString& Pair : Pairs)
	{
		FString Key, Value;
		if (!Pair.Split(TEXT("="), &Key, &Value))
		{
			continue;
		}
		const int32 N = FCString::Atoi(*Value);
		if (Key == TEXT("bc")) bCustomBeamColor = N != 0;
		else if (Key == TEXT("bcol")) BeamColor = ParseColor(Value, BeamColor);
		else if (Key == TEXT("bs")) BeamStyle = static_cast<uint8>(N);
		else if (Key == TEXT("cr")) bCustomRifle = N != 0;
		else if (Key == TEXT("rb")) RifleBody = ParseColor(Value, RifleBody);
		else if (Key == TEXT("ra")) RifleAccent = ParseColor(Value, RifleAccent);
		else if (Key == TEXT("rc")) RifleCore = ParseColor(Value, RifleCore);
		else if (Key == TEXT("rf")) RifleFinish = static_cast<uint8>(N);
		else if (Key == TEXT("ba")) Barrel = static_cast<uint8>(N);
		else if (Key == TEXT("st")) Stock = static_cast<uint8>(N);
		else if (Key == TEXT("fi")) Fins = static_cast<uint8>(N);
		else if (Key == TEXT("ch")) Charm = static_cast<uint8>(N);
		else if (Key == TEXT("rl")) RifleLivery = static_cast<uint8>(N);
		else if (Key == TEXT("kc")) bKillCounter = N != 0;
		else if (Key == TEXT("ke")) KillEffect = static_cast<uint8>(N);
		else if (Key == TEXT("cv")) CharacterVariant = static_cast<uint8>(N);
		else if (Key == TEXT("rk")) Rank = static_cast<uint8>(N);
		else if (Key == TEXT("ti")) TitleId = N;
	}
}
