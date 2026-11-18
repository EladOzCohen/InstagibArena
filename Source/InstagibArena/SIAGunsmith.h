// Instagib Arena

#pragma once

#include "CoreMinimal.h"
#include "IACosmetics.h"
#include "IALoadoutRules.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class APlayerController;

/**
 * The Gunsmith (docs/REWARDS_DESIGN.md 5.1, 5.2, 5.3, 6.1): every field of the cosmetic loadout, with a live 3D look at the rifle in the
 * hands of the preview character of the main menu (AIAMenuPlayerController moves the camera there while this widget exists).
 * Locked options are shown greyed with what is still needed ("500 kills"). SAVE stores the loadout in the profile
 * (UIAProfileSubsystem::SetLoadout); RESET goes back to the standard look; two saved designs after reward G4.
 *
 * A self-contained widget: the main menu shows it as its own screen (Character > GUNSMITH), and it can be put inside any other screen
 * of the main menu (for example the Hall of Champions): SNew(SIAGunsmith).OwnerController(Owner).OnBack(...).
 */
class SIAGunsmith : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIAGunsmith) : _ShowTitle(true) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, OwnerController)
		/** The BACK button (none when not set). Unsaved changes are dropped. */
		SLATE_ARGUMENT(TFunction<void()>, OnBack)
		/** Shows the "GUNSMITH" heading (leave it out when the host screen has its own). */
		SLATE_ARGUMENT(bool, ShowTitle)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual ~SIAGunsmith();

	/** The loadout being edited (not saved yet). */
	const FIACosmeticLoadout& GetWorkingLoadout() const { return Working; }

private:
	using EField = IALoadout::EField;

	TSharedRef<SWidget> BuildBody();
	TSharedRef<SWidget> BuildFooter();
	TSharedRef<SWidget> Section(const FText& Title);
	TSharedRef<SWidget> FieldRow(const FText& Label, EField Field);
	TSharedRef<SWidget> BeamColorRow();
	TSharedRef<SWidget> ColorRow(const FText& Label, FColor FIACosmeticLoadout::* Member);
	TSharedRef<SWidget> SlotsRow();
	TSharedRef<SWidget> LockedChip(const FText& Label, FName Reward) const;
	TSharedRef<SWidget> LockNote(TFunction<FText()> Text) const;

	bool Has(FName Reward) const;
	void Changed();
	void Save();
	void Reset();
	void StoreSlot(int32 Slot);
	void LoadSlot(int32 Slot);
	bool IsDirty() const;

	TWeakObjectPtr<APlayerController> Owner;
	TFunction<void()> OnBack;
	FIACosmeticLoadout Working;
	FIACosmeticLoadout Saved;
	FText Status;
	double StatusUntil = 0.0;
};
