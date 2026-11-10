// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineBaseTypes.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "IAMenuStateSubsystem.generated.h"

class UNetDriver;

/**
 * Remembers why the last network connection failed, so that the main menu can say so.
 * When a connection fails or is lost, Unreal sends the player back to the default map
 * (the main menu), and this subsystem survives that trip.
 */
UCLASS()
class INSTAGIBARENA_API UIAMenuStateSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** The last error as a sentence for the player. Empty after it has been taken once. */
	FString ConsumeError();

private:
	void OnNetworkFailure(UWorld* World, UNetDriver* NetDriver, ENetworkFailure::Type FailureType, const FString& ErrorString);
	void OnTravelFailure(UWorld* World, ETravelFailure::Type FailureType, const FString& ErrorString);

	FString LastError;
};
