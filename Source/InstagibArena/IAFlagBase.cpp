// Instagib Arena

#include "IAFlagBase.h"

AIAFlagBase::AIAFlagBase()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
}
