import pytest
from django.contrib.auth import SESSION_KEY, get_user_model

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
def test_successful_login_redirects_to_home(client, family_member):
    response = client.post(
        "/login/", {"username": "kid", "password": "correct-horse"}
    )

    assert response.status_code == 302
    assert response.url == "/"
    assert SESSION_KEY in client.session


@pytest.mark.django_db
def test_failed_login_with_wrong_password_creates_no_session(client, family_member):
    response = client.post("/login/", {"username": "kid", "password": "wrong"})

    assert response.status_code == 200
    assert SESSION_KEY not in client.session
    assert "didn't match" in response.content.decode()


@pytest.mark.django_db
def test_failed_login_with_nonexistent_username_creates_no_session(client):
    response = client.post(
        "/login/", {"username": "nobody", "password": "whatever"}
    )

    assert response.status_code == 200
    assert SESSION_KEY not in client.session


@pytest.mark.django_db
def test_failed_login_does_not_reveal_whether_username_exists(client, family_member):
    wrong_password_response = client.post(
        "/login/", {"username": "kid", "password": "wrong"}
    )
    nonexistent_user_response = client.post(
        "/login/", {"username": "nobody", "password": "whatever"}
    )

    assert (
        wrong_password_response.context["form"].errors
        == nonexistent_user_response.context["form"].errors
    )


@pytest.mark.django_db
def test_logout_ends_session_and_subsequent_request_redirects_to_login(
    client, family_member
):
    client.force_login(family_member)

    response = client.post("/logout/")

    assert SESSION_KEY not in client.session
    assert response.status_code == 302

    home_response = client.get("/")
    assert home_response.status_code == 302
    assert home_response.url.startswith("/login/")
