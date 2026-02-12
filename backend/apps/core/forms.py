import logging
from typing import Any

from allauth.account.forms import (
    ConfirmLoginCodeForm,
    LoginForm,
    RequestLoginCodeForm,
    SignupForm,
)

logger = logging.getLogger(__name__)

INPUT = (
    "w-full rounded-2xl border border-arti-dark/15 bg-white px-4 py-3 text-sm "
    "focus:border-arti-dark focus:ring-0"
)


class StyledLoginForm(LoginForm):
    """Passwordless login form with consistent styling."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        if "login" in self.fields:
            self.fields["login"].widget.attrs["placeholder"] = "you@example.com"


class StyledSignupForm(SignupForm):
    """Passwordless signup form with email and optional profile fields."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        if "email" in self.fields:
            self.fields["email"].widget.attrs["placeholder"] = "you@example.com"

        if "first_name" in self.fields:
            self.fields["first_name"].widget.attrs["placeholder"] = "First name"

        if "last_name" in self.fields:
            self.fields["last_name"].widget.attrs["placeholder"] = "Last name"

        removed_fields = []
        for name in list(self.fields.keys()):
            if "password" in name.lower():
                self.fields.pop(name, None)
                removed_fields.append(name)

        if removed_fields:
            logger.debug(
                f"Removed password fields from signup form: {removed_fields}. "
                "Ensure passwordless auth is configured correctly."
            )


class StyledRequestLoginCodeForm(RequestLoginCodeForm):
    """Styled form for requesting a login code."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT
        if "email" in self.fields:
            self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        if "login" in self.fields:
            self.fields["login"].widget.attrs["placeholder"] = "you@example.com"


class StyledConfirmLoginCodeForm(ConfirmLoginCodeForm):
    """Styled form for confirming a login code."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT
        if "code" in self.fields:
            self.fields["code"].widget.attrs.update(
                {
                    "placeholder": "123456",
                    "inputmode": "numeric",
                    "autocomplete": "one-time-code",
                }
            )
