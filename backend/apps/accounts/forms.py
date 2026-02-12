from django import forms

from .models import Address, CustomerProfile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ["phone"]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "label",
            "first_name",
            "last_name",
            "phone",
            "line1",
            "line2",
            "city",
            "postal_code",
            "region",
            "country",
            "is_default",
        ]
