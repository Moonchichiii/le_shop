import pytest
from django.db import IntegrityError, transaction

from backend.apps.accounts.models import Address, CustomerProfile
from backend.apps.accounts.tests.factories import AddressFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestCustomerProfile:
    def test_profile_created_on_user_save(self):
        user = UserFactory()
        assert CustomerProfile.objects.filter(user=user).exists()

    def test_profile_str(self):
        user = UserFactory()
        assert str(user.profile) == f"Profile<{user.id}>"


class TestAddress:
    def test_str_with_label(self, user):
        addr = AddressFactory(user=user, label="Work", city="Tunis")
        assert "Work" in str(addr)

    def test_str_falls_back_to_city(self, user):
        addr = AddressFactory(user=user, label="", city="Tunis")
        assert "Tunis" in str(addr)

    def test_default_ordering(self, user):
        """Default addresses come first, then most recent."""
        old = AddressFactory(user=user, is_default=False, label="Old")
        default = AddressFactory(user=user, is_default=True, label="Default")
        recent = AddressFactory(user=user, is_default=False, label="Recent")

        qs = Address.objects.filter(user=user)
        assert list(qs) == [default, recent, old]

    def test_setting_default_does_not_auto_unset_others(self, user):
        """Model layer doesn't enforce single-default — views do."""
        a1 = AddressFactory(user=user, is_default=True)
        with pytest.raises(IntegrityError), transaction.atomic():
            AddressFactory(user=user, is_default=True)

        # First one remains True
        a1.refresh_from_db()
        assert a1.is_default is True


class TestDefaultAddressConstraint:
    """DB-level guarantee: one default address per user."""

    def test_second_default_raises_integrity_error(self, user):
        AddressFactory(user=user, is_default=True)
        with pytest.raises(IntegrityError), transaction.atomic():
            AddressFactory(user=user, is_default=True)

    def test_different_users_can_each_have_a_default(self, user, other_user):
        AddressFactory(user=user, is_default=True)
        AddressFactory(user=other_user, is_default=True)
        # no error — constraint is per-user

    def test_multiple_non_default_allowed(self, user):
        AddressFactory(user=user, is_default=False)
        AddressFactory(user=user, is_default=False)
        assert Address.objects.filter(user=user).count() == 2
