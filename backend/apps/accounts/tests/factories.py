import factory
from django.contrib.auth import get_user_model

from backend.apps.accounts.models import Address

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123")
        user = model_class(**kwargs)
        user.set_password(password)
        user.save()
        return user


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    user = factory.SubFactory(UserFactory)
    label = "Home"
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    line1 = factory.Faker("street_address")
    city = factory.Faker("city")
    postal_code = factory.Faker("postcode")
    country = "FR"
    is_default = False
