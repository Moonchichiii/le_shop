from allauth.account.forms import LoginForm, SignupForm
from django import forms

INPUT = (
    "w-full rounded-2xl border border-arti-dark/15 bg-white px-4 py-3 text-sm "
    "focus:border-arti-dark focus:ring-0"
)


def is_password_widget(widget: forms.Widget) -> bool:
    return (
        isinstance(widget, forms.PasswordInput)
        or getattr(widget, "input_type", "") == "password"
    )


class StyledLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        if "login" in self.fields:
            self.fields["login"].widget.attrs["placeholder"] = "you@example.com"

        for name, field in self.fields.items():
            if is_password_widget(field.widget) or "password" in name:
                field.widget = forms.PasswordInput(
                    attrs={"class": INPUT, "placeholder": "••••••••"}
                )


class StyledSignupForm(SignupForm):
    """
    Supports two signup modes:
    - auth_method=code (default): password fields are optional
    - auth_method=password: password fields are required + must match
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        if "email" in self.fields:
            self.fields["email"].widget.attrs["placeholder"] = "you@example.com"

        # Identify password-ish fields
        self.password_field_names = [
            name
            for name, f in self.fields.items()
            if is_password_widget(f.widget) or "password" in name
        ]

        # Style them + make optional by default
        for i, name in enumerate(self.password_field_names):
            placeholder = "Create a password" if i == 0 else "Repeat password"
            self.fields[name].required = False
            self.fields[name].widget = forms.PasswordInput(
                attrs={"class": INPUT, "placeholder": placeholder}
            )

    def clean(self):
        cleaned = super().clean()

        method = self.data.get("auth_method", "code")  # "code" | "password"
        if method != "password":
            return cleaned

        # If user chose password mode, enforce it.
        pw_values = [
            cleaned.get(n) for n in self.password_field_names if cleaned.get(n)
        ]
        if len(pw_values) < 2:
            raise forms.ValidationError(
                "Please create a password (or choose email code sign-in)."
            )

        if pw_values[0] != pw_values[1]:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned
