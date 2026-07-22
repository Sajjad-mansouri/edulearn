import factory

from courses.models import Category, Tag


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    parent = None
    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = factory.Faker("sentence")
    display_order = factory.Sequence(lambda n: n)
    is_active = True


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")
