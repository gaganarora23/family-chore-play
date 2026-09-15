import pytest
from django.contrib.auth import get_user_model

from chores.models import FamilyMember, Household

User = get_user_model()


@pytest.fixture
def family_member(db):
    household = Household.objects.create(name='The Smiths')
    user = User.objects.create_user(username='kid', password='correct-horse')
    FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )
    return user


@pytest.mark.django_db
def test_home_page_returns_200_for_logged_in_user(client, family_member):
    client.force_login(family_member)

    response = client.get("/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_home_page_redirects_anonymous_user_to_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url.startswith("/login/")
