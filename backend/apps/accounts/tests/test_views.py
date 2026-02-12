import pytest
from django.urls import reverse

from backend.apps.accounts.models import Address, User
from backend.apps.accounts.tests.factories import AddressFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestLoginRequired:
    URLS = [
        "accounts:settings",
        "accounts:address-list",
        "accounts:address-create",
        "accounts:email-change",
        "accounts:danger-zone",
    ]

    @pytest.mark.parametrize("url_name", URLS)
    def test_redirects_anonymous(self, client, url_name: str) -> None:  # type: ignore[no-untyped-def]
        resp = client.get(reverse(url_name))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url or "/account" in resp.url

    def test_address_update_redirects_anonymous(
        self,
        client,
        address: Address,  # type: ignore[no-untyped-def]
    ) -> None:
        resp = client.get(reverse("accounts:address-update", args=[address.pk]))
        assert resp.status_code == 302

    def test_address_delete_redirects_anonymous(
        self,
        client,
        address: Address,  # type: ignore[no-untyped-def]
    ) -> None:
        resp = client.get(reverse("accounts:address-delete", args=[address.pk]))
        assert resp.status_code == 302


class TestSettingsView:
    def test_get(self, client, user: User) -> None:  # type: ignore[no-untyped-def]
        client.force_login(user)
        resp = client.get(reverse("accounts:settings"))
        assert resp.status_code == 200

    def test_update_phone(self, client, user: User) -> None:  # type: ignore[no-untyped-def]
        client.force_login(user)
        resp = client.post(
            reverse("accounts:settings"),
            {"phone": "+216 55 123 456"},
        )
        assert resp.status_code == 302
        user.profile.refresh_from_db()  # type: ignore[union-attr]
        assert user.profile.phone == "+216 55 123 456"  # type: ignore[union-attr]


class TestAddressList:
    def test_shows_own_addresses(self, client, user: User) -> None:  # type: ignore[no-untyped-def]
        AddressFactory.create(user=user, label="Home")
        AddressFactory.create(user=user, label="Work")
        client.force_login(user)
        resp = client.get(reverse("accounts:address-list"))
        assert resp.status_code == 200
        assert b"Home" in resp.content
        assert b"Work" in resp.content

    def test_does_not_show_other_users_addresses(
        self,
        client,
        user: User,  # type: ignore[no-untyped-def]
    ) -> None:
        other: User = UserFactory.create()  # type: ignore[assignment]
        AddressFactory.create(user=other, label="Secret")
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

    def test_create_address(self, client, user: User) -> None:  # type: ignore[no-untyped-def]
        client.force_login(user)
        resp = client.post(
            reverse("accounts:address-create"),
            self.VALID_DATA,
        )
        assert resp.status_code == 302
        assert Address.objects.filter(user=user, city="Tunis").exists()

    def test_create_default_unsets_previous(
        self,
        client,
        user: User,  # type: ignore[no-untyped-def]
    ) -> None:
        old: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, is_default=True
        )
        client.force_login(user)
        client.post(
            reverse("accounts:address-create"),
            self.VALID_DATA,
        )
        old.refresh_from_db()
        assert old.is_default is False

        new = Address.objects.filter(user=user, city="Tunis").first()
        assert new is not None
        assert new.is_default is True


class TestAddressUpdate:
    def test_update_own_address(
        self,
        client,
        user: User,
        address: Address,  # type: ignore[no-untyped-def]
    ) -> None:
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

    def test_cannot_update_other_users_address(
        self,
        client,
        user: User,
        other_user: User,  # type: ignore[no-untyped-def]
    ) -> None:
        addr: Address = AddressFactory.create(  # type: ignore[assignment]
            user=other_user
        )
        client.force_login(user)
        resp = client.get(reverse("accounts:address-update", args=[addr.pk]))
        assert resp.status_code == 404


class TestAddressDelete:
    def test_delete_own_address(
        self,
        client,
        user: User,
        address: Address,  # type: ignore[no-untyped-def]
    ) -> None:
        client.force_login(user)
        resp = client.post(reverse("accounts:address-delete", args=[address.pk]))
        assert resp.status_code == 302
        assert not Address.objects.filter(pk=address.pk).exists()

    def test_cannot_delete_other_users_address(
        self,
        client,
        user: User,
        other_user: User,  # type: ignore[no-untyped-def]
    ) -> None:
        addr: Address = AddressFactory.create(  # type: ignore[assignment]
            user=other_user
        )
        client.force_login(user)
        resp = client.post(reverse("accounts:address-delete", args=[addr.pk]))
        assert resp.status_code == 404
        assert Address.objects.filter(pk=addr.pk).exists()


class TestDangerZone:
    def test_get_renders(self, client, user: User) -> None:  # type: ignore[no-untyped-def]
        client.force_login(user)
        resp = client.get(reverse("accounts:danger-zone"))
        assert resp.status_code == 200

    def test_wrong_confirmation_keeps_account(
        self,
        client,
        user: User,  # type: ignore[no-untyped-def]
    ) -> None:
        client.force_login(user)
        client.post(
            reverse("accounts:danger-zone"),
            {"confirmation": "NOPE"},
        )
        from django.contrib.auth import get_user_model

        assert get_user_model().objects.filter(pk=user.pk).exists()

    def test_correct_confirmation_deletes_account(
        self,
        client,
        user: User,  # type: ignore[no-untyped-def]
    ) -> None:
        client.force_login(user)
        resp = client.post(
            reverse("accounts:danger-zone"),
            {"confirmation": "DELETE"},
        )
        assert resp.status_code == 302
        from django.contrib.auth import get_user_model

        assert not get_user_model().objects.filter(pk=user.pk).exists()
