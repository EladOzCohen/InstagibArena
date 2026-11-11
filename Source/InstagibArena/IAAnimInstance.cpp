// Instagib Arena

#include "IAAnimInstance.h"
#include "IAPlayerCharacter.h"
#include "IACharacterMovement.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNodeBase.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"

namespace
{
	/** Index of every clip the animation uses. */
	enum EClip : int32
	{
		Jog0 = 0,         // 8 directions: Fwd, FwdRight, Right, BwdRight, Bwd, BwdLeft, Left, FwdLeft
		Walk0 = 8,        // the same 8 directions, walking
		Idle = 16,
		JumpStart,
		JumpLoop,
		FallLoop,
		FallLand,
		AimDown,
		AimUp,
		ClipCount
	};

	const TCHAR* const DirNames[8] = { TEXT("Fwd"), TEXT("Fwd_Right"), TEXT("Right"), TEXT("Bwd_Right"), TEXT("Bwd"), TEXT("Bwd_Left"), TEXT("Left"), TEXT("Fwd_Left") };

	// Each walk and jog clip holds several strides. A stride is one left step plus one right step.
	const float JogCycles[8]  = { 3, 3, 2, 4, 4, 4, 1, 3 };
	const float WalkCycles[8] = { 2, 2, 2, 2, 2, 2, 2, 2 };

	// Where inside a stride the left foot is down. Shifting every clip by it keeps the feet of neighbouring directions in step.
	const float JogFootDown[8]  = { 0.467f, 0.467f, 0.875f, 0.59f, 0.59f, 0.59f, 0.64f, 0.467f };
	const float WalkFootDown[8] = { 0.70f, 0.70f, 0.22f, 0.17f, 0.17f, 0.17f, 0.38f, 0.70f };

	// Distance covered in one stride (cm): the play rate follows the speed, so the feet do not slide.
	constexpr float JogStride = 300.f;
	constexpr float WalkStride = 230.f;
	constexpr float WalkSpeed = 295.f;   // speed at which the walk clips look right
	constexpr float JogSpeed = 600.f;

	const TCHAR* const ClipDir = TEXT("/Game/Characters/Mannequins/Anims/Rifle/");
}

/** The part that really works: it lives with the animation instance, evaluates the clips and blends them. */
struct FIAAnimProxy : public FAnimInstanceProxy
{
	FIAAnimProxy() {}
	explicit FIAAnimProxy(UAnimInstance* InInstance) : FAnimInstanceProxy(InInstance) {}

	UAnimSequence* Clips[ClipCount] = {};

	// ---- inputs, copied from the pawn on the game thread
	bool bHasPawn = false;
	float RawSpeed = 0.f;
	float RawDir = 0.f;
	float VelZ = 0.f;
	bool bGrounded = true;
	bool bCrouched = false;
	float AimPitch = 0.f;
	bool bLandEvent = false;
	float LandImpact = 0.f;

	// ---- state kept between frames
	float Speed = 0.f;
	float Dir = 0.f;
	float Phase = 0.f;
	float IdleTime = 0.f;
	float CrouchAlpha = 0.f;
	float AirAlpha = 0.f;
	float AirTime = 0.f;
	float LandTimer = 99.f;
	float LandStrength = 0.f;
	float PrevVelZ = 0.f;
	bool bPrevGrounded = true;

	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override
	{
		FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);

		const AIAPlayerCharacter* Pawn = Cast<AIAPlayerCharacter>(InAnimInstance->TryGetPawnOwner());
		bHasPawn = Pawn != nullptr;
		if (!Pawn)
		{
			return;
		}

		const FVector Velocity = Pawn->GetVelocity();
		const FVector Local = Pawn->GetActorRotation().UnrotateVector(Velocity);
		RawSpeed = Velocity.Size2D();
		RawDir = FMath::RadiansToDegrees(FMath::Atan2(Local.Y, Local.X));
		VelZ = Velocity.Z;
		const UCharacterMovementComponent* Move = Pawn->GetCharacterMovement();
		bGrounded = Move && Move->IsMovingOnGround();
		bCrouched = Pawn->bIsCrouched;
		AimPitch = FRotator::NormalizeAxis(Pawn->GetAimPitchForAnimation());

		// A landing is a fall that ends on the ground.
		if (bGrounded && !bPrevGrounded && PrevVelZ < -300.f)
		{
			bLandEvent = true;
			LandImpact = -PrevVelZ;
		}
		bPrevGrounded = bGrounded;
		PrevVelZ = VelZ;
	}

	virtual void Update(float DeltaSeconds) override
	{
		if (!bHasPawn)
		{
			return;
		}
		const float Dt = FMath::Min(DeltaSeconds, 0.1f);

		Speed = FMath::FInterpTo(Speed, RawSpeed, Dt, 14.f);
		if (RawSpeed > 25.f)
		{
			Dir += FMath::FInterpTo(0.f, FMath::FindDeltaAngleDegrees(Dir, RawDir), Dt, 16.f);
			Dir = FRotator::NormalizeAxis(Dir);
		}

		// Stride rate: how many strides per second the feet make at this speed.
		const float JogWeight = FMath::Clamp((Speed - WalkSpeed) / (JogSpeed - WalkSpeed), 0.f, 1.f);
		const float Stride = FMath::Lerp(WalkStride, JogStride, JogWeight);
		Phase = FMath::Frac(Phase + Dt * FMath::Min(Speed, 650.f) / Stride);
		IdleTime += Dt;

		CrouchAlpha = FMath::FInterpConstantTo(CrouchAlpha, bCrouched ? 1.f : 0.f, Dt, 7.f);

		if (bGrounded)
		{
			AirTime = 0.f;
		}
		else
		{
			AirTime += Dt;
		}
		AirAlpha = FMath::FInterpTo(AirAlpha, AirTime > 0.08f ? 1.f : 0.f, Dt, 14.f);

		if (bLandEvent)
		{
			bLandEvent = false;
			LandTimer = 0.f;
			LandStrength = FMath::Clamp((LandImpact - 250.f) / 700.f, 0.3f, 1.f);
		}
		LandTimer += Dt;
	}

	// ---- helpers for Evaluate

	static void Sample(const UAnimSequence* Sequence, float Time, FPoseContext& Out)
	{
		if (!Sequence)
		{
			Out.ResetToRefPose();
			return;
		}
		const float Length = Sequence->GetPlayLength();
		const float T = Length > 0.f ? FMath::Fmod(FMath::Max(Time, 0.f), Length) : 0.f;
		FAnimationPoseData Data(Out);
		FAnimExtractContext Context(static_cast<double>(T), false, FDeltaTimeRecord(), true);
		Sequence->GetAnimationPose(Data, Context);
	}

	static void Blend(FPoseContext& InOut, FPoseContext& Other, float WeightOfOther)
	{
		if (WeightOfOther <= 0.001f)
		{
			return;
		}
		FAnimationPoseData A(InOut);
		FAnimationPoseData B(Other);
		FAnimationRuntime::BlendTwoPosesTogetherInPlace(A, B, 1.f - WeightOfOther);
	}

	/** Walk or jog in the current direction: the two neighbouring direction clips, shifted to the same stride. */
	void SampleGait(bool bJog, FPoseContext& Target, FPoseContext& Scratch) const
	{
		const float Pos = FMath::Fmod(Dir + 360.f, 360.f) / 45.f;
		const int32 First = FMath::FloorToInt(Pos) % 8;
		const int32 Second = (First + 1) % 8;
		const float Fraction = Pos - FMath::FloorToInt(Pos);

		const float* Cycles = bJog ? JogCycles : WalkCycles;
		const float* Foot = bJog ? JogFootDown : WalkFootDown;
		const int32 Base = bJog ? Jog0 : Walk0;

		for (int32 K = 0; K < 2; ++K)
		{
			const int32 Index = K == 0 ? First : Second;
			const UAnimSequence* Clip = Clips[Base + Index];
			const float Cycle = Clip ? Clip->GetPlayLength() / Cycles[Index] : 1.f;
			const float Time = (Foot[Index] + Phase) * Cycle;
			Sample(Clip, Time, K == 0 ? Target : Scratch);
		}
		Blend(Target, Scratch, Fraction);
	}

	virtual bool Evaluate(FPoseContext& Output) override
	{
		Output.ResetToRefPose();
		if (!bHasPawn || !Clips[Idle])
		{
			return true;
		}

		FPoseContext A(Output);
		FPoseContext B(Output);

		// ---- on the ground: idle, walk and jog blended by speed
		const float WalkWeight = FMath::Clamp((Speed - 15.f) / (WalkSpeed - 15.f), 0.f, 1.f);
		const float JogWeight = FMath::Clamp((Speed - WalkSpeed) / (JogSpeed - WalkSpeed), 0.f, 1.f);
		const float WIdle = 1.f - WalkWeight;
		const float WWalk = WalkWeight * (1.f - JogWeight);
		const float WJog = WalkWeight * JogWeight;

		float Accumulated = 0.f;
		auto Add = [&](float Weight, bool bIsIdle, bool bJog)
		{
			if (Weight <= 0.002f)
			{
				return;
			}
			FPoseContext& Target = Accumulated <= 0.f ? Output : A;
			if (bIsIdle)
			{
				Sample(Clips[Idle], IdleTime, Target);
			}
			else
			{
				SampleGait(bJog, Target, B);
			}
			if (Accumulated > 0.f)
			{
				Blend(Output, A, Weight / (Accumulated + Weight));
			}
			Accumulated += Weight;
		};
		Add(WIdle, true, false);
		Add(WWalk, false, false);
		Add(WJog, false, true);

		// ---- crouch: a frozen deep-knee pose
		if (CrouchAlpha > 0.01f)
		{
			Sample(Clips[FallLand], 0.17f, A);
			Blend(Output, A, FMath::InterpEaseInOut(0.f, 1.f, CrouchAlpha, 2.f));
		}

		// ---- landing: the legs absorb the impact
		if (LandTimer < 0.4f && AirAlpha < 0.5f)
		{
			const float Fade = LandTimer < 0.12f ? 1.f : 1.f - (LandTimer - 0.12f) / 0.28f;
			Sample(Clips[FallLand], LandTimer, A);
			Blend(Output, A, LandStrength * Fade * 0.9f);
		}

		// ---- in the air: rising, then falling
		if (AirAlpha > 0.01f)
		{
			const UAnimSequence* Start = Clips[JumpStart];
			const float StartLength = Start ? Start->GetPlayLength() : 0.2f;
			if (AirTime < StartLength)
			{
				Sample(Start, AirTime, A);
			}
			else
			{
				Sample(Clips[JumpLoop], AirTime - StartLength, A);
			}
			Sample(Clips[FallLoop], AirTime * 2.f, B);
			const float Falling = FMath::Clamp((100.f - VelZ) / 300.f, 0.f, 1.f);
			Blend(A, B, Falling);
			Blend(Output, A, AirAlpha);
		}

		// ---- aim: the upper body follows the view pitch (additive clips, up and down)
		const float Up = FMath::Clamp(AimPitch / 60.f, 0.f, 1.f);
		const float Down = FMath::Clamp(-AimPitch / 60.f, 0.f, 1.f);
		for (int32 K = 0; K < 2; ++K)
		{
			const UAnimSequence* Aim = Clips[K == 0 ? AimUp : AimDown];
			const float Weight = K == 0 ? Up : Down;
			if (Aim && Weight > 0.01f)
			{
				Sample(Aim, 0.f, A);
				FAnimationPoseData OutData(Output);
				FAnimationPoseData AimData(A);
				FAnimationRuntime::AccumulateAdditivePose(OutData, AimData, Weight, Aim->AdditiveAnimType);
			}
		}
		Output.Pose.NormalizeRotations();
		return true;
	}
};

FAnimInstanceProxy* UIAAnimInstance::CreateAnimInstanceProxy()
{
	FIAAnimProxy* Proxy = new FIAAnimProxy(this);

	auto Load = [this](const FString& Name) -> UAnimSequence*
	{
		UAnimSequence* Sequence = LoadObject<UAnimSequence>(nullptr, *(FString(ClipDir) + Name));
		if (Sequence)
		{
			Clips.AddUnique(Sequence);
		}
		return Sequence;
	};

	for (int32 I = 0; I < 8; ++I)
	{
		Proxy->Clips[Jog0 + I] = Load(FString::Printf(TEXT("Jog/MF_Rifle_Jog_%s.MF_Rifle_Jog_%s"), DirNames[I], DirNames[I]));
		Proxy->Clips[Walk0 + I] = Load(FString::Printf(TEXT("Walk/MF_Rifle_Walk_%s.MF_Rifle_Walk_%s"), DirNames[I], DirNames[I]));
	}
	Proxy->Clips[Idle] = Load(TEXT("MF_Rifle_Idle_ADS.MF_Rifle_Idle_ADS"));
	Proxy->Clips[JumpStart] = Load(TEXT("Jump/MM_Rifle_Jump_Start.MM_Rifle_Jump_Start"));
	Proxy->Clips[JumpLoop] = Load(TEXT("Jump/MM_Rifle_Jump_Start_Loop.MM_Rifle_Jump_Start_Loop"));
	Proxy->Clips[FallLoop] = Load(TEXT("Jump/MM_Rifle_Jump_Fall_Loop.MM_Rifle_Jump_Fall_Loop"));
	Proxy->Clips[FallLand] = Load(TEXT("Jump/MM_Rifle_Jump_Fall_Land.MM_Rifle_Jump_Fall_Land"));
	Proxy->Clips[AimDown] = Load(TEXT("AIM/MM_Rifle_Idle_ADS_AO_CD.MM_Rifle_Idle_ADS_AO_CD"));
	Proxy->Clips[AimUp] = Load(TEXT("AIM/MM_Rifle_Idle_ADS_AO_CU.MM_Rifle_Idle_ADS_AO_CU"));
	return Proxy;
}
