from app.models.enums import RegistrationStatus, ReviewAction


FLOW = {
    RegistrationStatus.submitted: {ReviewAction.supplement: RegistrationStatus.supplemented, ReviewAction.approve: RegistrationStatus.approved, ReviewAction.reject: RegistrationStatus.rejected, ReviewAction.cancel: RegistrationStatus.canceled},
    RegistrationStatus.supplemented: {ReviewAction.approve: RegistrationStatus.approved, ReviewAction.reject: RegistrationStatus.rejected, ReviewAction.cancel: RegistrationStatus.canceled},
    RegistrationStatus.rejected: {ReviewAction.promote: RegistrationStatus.promoted_from_waitlist},
}


def next_status(current: RegistrationStatus, action: ReviewAction) -> RegistrationStatus:
    if current not in FLOW or action not in FLOW[current]:
        raise ValueError(f"Invalid transition: {current} -> {action}")
    return FLOW[current][action]
