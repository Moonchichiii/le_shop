import pytest
from django.db import IntegrityError, transaction

from backend.apps.accounts.models import Address, CustomerProfile, User
from backend.apps.accounts.tests.factories import AddressFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestCustomerProfile:
    def test_profile_created_on_user_save(self) -> None:
        user: User = UserFactory.create()  # type: ignore[assignment]
        assert CustomerProfile.objects.filter(user=user).exists()

    def test_profile_str(self) -> None:
        user: User = UserFactory.create()  # type: ignore[assignment]
        assert str(user.profile) == f"Profile<{user.id}>"


class TestAddress:
    def test_str_with_label(self, user: User) -> None:
        addr: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, label="Work", city="Tunis"
        )
        assert "Work" in str(addr)

    def test_str_falls_back_to_city(self, user: User) -> None:
        addr: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, label="", city="Tunis"
        )
        assert "Tunis" in str(addr)

    def test_default_ordering(self, user: User) -> None:
        old: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, is_default=False, label="Old"
        )
        default: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, is_default=True, label="Default"
        )
        recent: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, is_default=False, label="Recent"
        )

        qs = Address.objects.filter(user=user)
        assert list(qs) == [default, recent, old]

    def test_setting_default_does_not_auto_unset_others(self, user: User) -> None:
        a1: Address = AddressFactory.create(  # type: ignore[assignment]
            user=user, is_default=True
        )
        with pytest.raises(IntegrityError), transaction.atomic():
            AddressFactory.create(user=user, is_default=True)

        a1.refresh_from_db()
        assert a1.is_default is True


class TestDefaultAddressConstraint:
    def test_second_default_raises_integrity_error(self, user: User) -> None:
        AddressFactory.create(user=user, is_default=True)
        with pytest.raises(IntegrityError), transaction.atomic():
            AddressFactory.create(user=user, is_default=True)

    def test_different_users_can_each_have_a_default(
        self, user: User, other_user: User
    ) -> None:
        AddressFactory.create(user=user, is_default=True)
        AddressFactory.create(user=other_user, is_default=True)

    def test_multiple_non_default_allowed(self, user: User) -> None:
        AddressFactory.create(user=user, is_default=False)
        AddressFactory.create(user=user, is_default=False)
        assert Address.objects.filter(user=user).count() == 2
