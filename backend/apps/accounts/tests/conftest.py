import pytest

from backend.apps.accounts.models import Address, User
from backend.apps.accounts.tests.factories import AddressFactory, UserFactory


@pytest.fixture
def user() -> User:
    return UserFactory.create()  # type: ignore[return-value]


@pytest.fixture
def other_user() -> User:
    return UserFactory.create()  # type: ignore[return-value]


@pytest.fixture
def address(user: User) -> Address:
    return AddressFactory.create(user=user)  # type: ignore[return-value]
