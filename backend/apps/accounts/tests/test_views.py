import pytest
from django.urls import reverse

from backend.apps.accounts.models import Address
from backend.apps.accounts.tests.factories import AddressFactory, UserFactory

pytestmark = pytest.mark.django_db


# ─── Auth guards ────────────────────────────────────────────


class TestLoginRequired:
    """All account views redirect anonymous users to login."""

    URLS = [
        "accounts:settings",
        "accounts:address-list",
        "accounts:address-create",
        "accounts:email-change",
        "accounts:danger-zone",
    ]

    @pytest.mark.parametrize("url_name", URLS)
    def test_redirects_anonymous(self, client, url_name):
        resp = client.get(reverse(url_name))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url or "/account" in resp.url

    def test_address_update_redirects_anonymous(self, client, address):
        resp = client.get(reverse("accounts:address-update", args=[address.pk]))
        assert resp.status_code == 302

    def test_address_delete_redirects_anonymous(self, client, address):
        resp = client.get(reverse("accounts:address-delete", args=[address.pk]))
        assert resp.status_code == 302


# ─── Settings ───────────────────────────────────────────────


class TestSettingsView:
    def test_get(self, client, user):
        client.force_login(user)
        resp = client.get(reverse("accounts:settings"))
        assert resp.status_code == 200

    def test_update_phone(self, client, user):
        client.force_login(user)
        resp = client.post(
            reverse("accounts:settings"),
            {"phone": "+216 55 123 456"},
        )
        assert resp.status_code == 302
        user.profile.refresh_from_db()
        assert user.profile.phone == "+216 55 123 456"


# ─── Address CRUD ───────────────────────────────────────────


class TestAddressList:
    def test_shows_own_addresses(self, client, user):
        AddressFactory(user=user, label="Home")
        AddressFactory(user=user, label="Work")
        client.force_login(user)
        resp = client.get(reverse("accounts:address-list"))
        assert resp.status_code == 200
        assert b"Home" in resp.content
        assert b"Work" in resp.content

    def test_does_not_show_other_users_addresses(self, client, user):
        other = UserFactory()
        AddressFactory(user=other, label="Secret")
        client.force_login(user)
        resp = client.get(reverse("accounts:address-list"))
        assert b"Secret" not in resp.content


class TestAddressCreate:
    VALID_DATA = {
        "label": "Home",
        "first_name": "Ali",
        "last_name": "Ben",
        "phone": "",
        "line1": "10 Rue de la Liberté",
        "line2": "",
        "city": "Tunis",
        "postal_code": "1000",
        "region": "",
        "country": "TN",
        "is_default": True,
    }

    def test_create_address(self, client, user):
        client.force_login(user)
        resp = client.post(
            reverse("accounts:address-create"),
            self.VALID_DATA,
        )
        assert resp.status_code == 302
        assert Address.objects.filter(user=user, city="Tunis").exists()

    def test_create_default_unsets_previous(self, client, user):
        old = AddressFactory(user=user, is_default=True)
        client.force_login(user)
        client.post(
            reverse("accounts:address-create"),
            self.VALID_DATA,
        )
        old.refresh_from_db()
        assert old.is_default is False

        new = Address.objects.filter(user=user, city="Tunis").first()
        assert new.is_default is True


class TestAddressUpdate:
    def test_update_own_address(self, client, user, address):
        client.force_login(user)
        resp = client.post(
            reverse("accounts:address-update", args=[address.pk]),
            {
                "label": "Updated",
                "first_name": address.first_name,
                "last_name": address.last_name,
                "phone": "",
                "line1": address.line1,
                "line2": "",
                "city": address.city,
                "postal_code": address.postal_code,
                "region": "",
                "country": address.country,
                "is_default": False,
            },
        )
        assert resp.status_code == 302
        address.refresh_from_db()
        assert address.label == "Updated"

    def test_cannot_update_other_users_address(self, client, user, other_user):
        addr = AddressFactory(user=other_user)
        client.force_login(user)
        resp = client.get(reverse("accounts:address-update", args=[addr.pk]))
        assert resp.status_code == 404


class TestAddressDelete:
    def test_delete_own_address(self, client, user, address):
        client.force_login(user)
        resp = client.post(reverse("accounts:address-delete", args=[address.pk]))
        assert resp.status_code == 302
        assert not Address.objects.filter(pk=address.pk).exists()

    def test_cannot_delete_other_users_address(self, client, user, other_user):
        addr = AddressFactory(user=other_user)
        client.force_login(user)
        resp = client.post(reverse("accounts:address-delete", args=[addr.pk]))
        assert resp.status_code == 404
        assert Address.objects.filter(pk=addr.pk).exists()


# ─── Danger zone ────────────────────────────────────────────


class TestDangerZone:
    def test_get_renders(self, client, user):
        client.force_login(user)
        resp = client.get(reverse("accounts:danger-zone"))
        assert resp.status_code == 200

    def test_wrong_confirmation_keeps_account(self, client, user):
        client.force_login(user)
        client.post(
            reverse("accounts:danger-zone"),
            {"confirmation": "NOPE"},
        )
        # redirects or re-renders — user still exists
        from django.contrib.auth import get_user_model

        assert get_user_model().objects.filter(pk=user.pk).exists()

    def test_correct_confirmation_deletes_account(self, client, user):
        client.force_login(user)
        resp = client.post(
            reverse("accounts:danger-zone"),
            {"confirmation": "DELETE"},
        )
        assert resp.status_code == 302
        from django.contrib.auth import get_user_model

        assert not get_user_model().objects.filter(pk=user.pk).exists()
