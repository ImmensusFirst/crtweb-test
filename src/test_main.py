from database import Base, City, User

from fastapi.testclient import TestClient

from main import app, get_db

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False,
                                   bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

TEST_CITY_1_NAME = 'Moscow'
TEST_CITY_2_NAME = 'Kazan'
TEST_USER_1_NAME = 'SuperUser'
TEST_USER_1_AGE = 50
TEST_USER_2_NAME = 'BaseUser'
TEST_USER_2_AGE = 20


class Test01Cities:
    def test_get_cities(self, test_db):
        test_city = City(name=TEST_CITY_1_NAME)
        db = TestingSessionLocal()
        db.add(test_city)
        db.commit()

        response = client.get("/cities/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['name'] == TEST_CITY_1_NAME
        assert 'weather' in ans[0]

    def test_post_city(self, test_db):
        response = client.post(
            "/cities/",
            json={"name": TEST_CITY_2_NAME, })
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 3
        assert ans['name'] == TEST_CITY_2_NAME
        assert 'weather' in ans

        response = client.get("/cities/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['name'] == TEST_CITY_2_NAME
        assert 'weather' in ans[0]

    def test_post_already_added_city(self, test_db):
        test_city = City(name=TEST_CITY_1_NAME)
        db = TestingSessionLocal()
        db.add(test_city)
        db.commit()

        response = client.post(
            "/cities/",
            json={"name": TEST_CITY_1_NAME, })
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 3
        assert ans['name'] == TEST_CITY_1_NAME
        assert 'weather' in ans

    def test_post_bad_city(self, test_db):
        response = client.post(
            "/cities/",
            json={"name": 'QQQ123', })
        assert response.status_code == 400


class Test02Users:
    def test_get_users(self, test_db):
        test_user = User(name=TEST_USER_1_NAME, surname=TEST_USER_1_NAME,
                         age=TEST_USER_1_AGE)
        db = TestingSessionLocal()
        db.add(test_user)
        db.commit()

        response = client.get("/users/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['name'] == TEST_USER_1_NAME
        assert ans[0]['surname'] == TEST_USER_1_NAME
        assert ans[0]['age'] == TEST_USER_1_AGE

    def test_post_user(self, test_db):
        response = client.post(
            "/users/",
            json={"name": TEST_USER_2_NAME, "surname": TEST_USER_2_NAME,
                  "age": TEST_USER_2_AGE})
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 4
        assert ans['name'] == TEST_USER_2_NAME
        assert ans['surname'] == TEST_USER_2_NAME
        assert ans['age'] == TEST_USER_2_AGE

        response = client.get("/users/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['name'] == TEST_USER_2_NAME
        assert ans[0]['surname'] == TEST_USER_2_NAME
        assert ans[0]['age'] == TEST_USER_2_AGE
