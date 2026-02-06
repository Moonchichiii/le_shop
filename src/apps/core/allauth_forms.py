from allauth.account.forms import LoginForm, SignupForm
from django import forms

# Added focus styles to your input class
INPUT = (
    "w-full rounded-2xl border border-arti-dark/15 bg-white px-4 py-3 text-sm"
    "focus:border-arti-dark focus:ring-0"
)


class StyledLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Apply base style to ALL fields present
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        # 2. Customize 'login' if it exists
        if "login" in self.fields:
            self.fields["login"].widget.attrs["placeholder"] = "you@example.com"

        # 3. Customize 'password' if it exists
        if "password" in self.fields:
            self.fields["password"].widget = forms.PasswordInput(
                attrs={"class": INPUT, "placeholder": "••••••••"}
            )


class StyledSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Apply base style to ALL fields (first_name, last_name, etc.)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

        # 2. Customize 'email'
        if "email" in self.fields:
            self.fields["email"].widget.attrs["placeholder"] = "you@example.com"

        # 3. Customize Password fields safely
        # Allauth usually uses 'password' and 'password_confirm' (not password1/2)

        if "password" in self.fields:
            self.fields["password"].widget = forms.PasswordInput(
                attrs={"class": INPUT, "placeholder": "Create a password"}
            )

        # Check for confirmation field (name varies by config, usually
        # 'password_confirm')
        for confirm in ["password_confirm", "confirm_password"]:
            if confirm in self.fields:
                self.fields[confirm].widget = forms.PasswordInput(
                    attrs={"class": INPUT, "placeholder": "Repeat password"}
                )
