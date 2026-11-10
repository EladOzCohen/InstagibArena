// Instagib Arena

#include "IAMenuStateSubsystem.h"
#include "InstagibArena.h"
#include "Engine/Engine.h"

void UIAMenuStateSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (GEngine)
	{
		GEngine->OnNetworkFailure().AddUObject(this, &UIAMenuStateSubsystem::OnNetworkFailure);
		GEngine->OnTravelFailure().AddUObject(this, &UIAMenuStateSubsystem::OnTravelFailure);
	}
}

void UIAMenuStateSubsystem::Deinitialize()
{
	if (GEngine)
	{
		GEngine->OnNetworkFailure().RemoveAll(this);
		GEngine->OnTravelFailure().RemoveAll(this);
	}
	Super::Deinitialize();
}

FString UIAMenuStateSubsystem::ConsumeError()
{
	FString Result = LastError;
	LastError.Reset();
	return Result;
}

void UIAMenuStateSubsystem::OnNetworkFailure(UWorld* World, UNetDriver* NetDriver, ENetworkFailure::Type FailureType, const FString& ErrorString)
{
	switch (FailureType)
	{
	case ENetworkFailure::ConnectionLost:
		LastError = TEXT("The connection to the host was lost.");
		break;
	case ENetworkFailure::ConnectionTimeout:
		LastError = TEXT("The connection timed out.");
		break;
	case ENetworkFailure::PendingConnectionFailure:
		LastError = TEXT("Could not connect. Check the address and that the host is running a game.");
		break;
	case ENetworkFailure::FailureReceived:
		LastError = TEXT("The host refused the connection.");
		break;
	default:
		LastError = TEXT("A network error happened.");
		break;
	}
	UE_LOG(LogInstagib, Warning, TEXT("Network failure %s: %s"), ENetworkFailure::ToString(FailureType), *ErrorString);
}

void UIAMenuStateSubsystem::OnTravelFailure(UWorld* World, ETravelFailure::Type FailureType, const FString& ErrorString)
{
	if (LastError.IsEmpty())
	{
		LastError = TEXT("Could not open the game. Check the address.");
	}
	UE_LOG(LogInstagib, Warning, TEXT("Travel failure %s: %s"), ETravelFailure::ToString(FailureType), *ErrorString);
}
