import pytest

from backend.apps.accounts.tests.factories import AddressFactory, UserFactory


@pytest.fixture()
def user(db):
    return UserFactory()


@pytest.fixture()
def other_user(db):
    return UserFactory()


@pytest.fixture()
def address(db, user):
    return AddressFactory(user=user)
