from allauth.account.forms import LoginForm, SignupForm

INPUT = (
    "w-full rounded-2xl border border-arti-dark/15 bg-white px-4 py-3 text-sm "
    "focus:border-arti-dark focus:ring-0"
)


class StyledLoginForm(LoginForm):
    """
    Passwordless login (email-only).

    Renders the Allauth LoginForm but ensures:
    - Consistent styling
    - Email placeholder
    - No password fields are relied on in templates/tests
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        if "login" in self.fields:
            self.fields["login"].widget.attrs["placeholder"] = "you@example.com"


class StyledSignupForm(SignupForm):
    """
    Passwordless signup (email + optional profile fields).

    We explicitly remove any password fields that Allauth might add,
    because this project is "magic link / code login" only.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style everything
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        # Placeholders
        if "email" in self.fields:
            self.fields["email"].widget.attrs["placeholder"] = "you@example.com"

        if "first_name" in self.fields:
            self.fields["first_name"].widget.attrs["placeholder"] = "First name"

        if "last_name" in self.fields:
            self.fields["last_name"].widget.attrs["placeholder"] = "Last name"

        # Hard remove any password-ish fields if present
        for name in list(self.fields.keys()):
            if "password" in name:
                self.fields.pop(name, None)
