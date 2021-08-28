import datetime as dt

from database import Base, City, Picnic, User

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
TEST_USER_3_NAME = 'User'
TEST_USER_3_AGE = 40
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class Test01Cities:
    def test_get_cities(self, test_db):
        """
        Проверка чтения списка городов
        """
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

    def test_create_city(self, test_db):
        """
        Проверка создание города
        """
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

    def test_create_already_added_city(self, test_db):
        """
        Проверка создания уже добавленного города
        """
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

    def test_create_bad_city(self, test_db):
        """
        Проверка создания несуществующего города
        """
        response = client.post(
            "/cities/",
            json={"name": 'QQQ123', })
        assert response.status_code == 400

    def test_search_city(self, test_db):
        """
        Проверка поиска города
        """
        test_city = City(name=TEST_CITY_1_NAME)
        db = TestingSessionLocal()
        db.add(test_city)
        db.commit()

        response = client.get(f"/cities/?q={TEST_CITY_1_NAME}")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['name'] == TEST_CITY_1_NAME


class Test02Users:
    def test_get_users(self, test_db):
        """
        Проверка получения списка пользователей
        """
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

    def test_create_user(self, test_db):
        """
        Проверка создания пользователя
        """
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

    def test_search_min_max(self, test_db):
        """
        Проверка поиска пользователя по min_age, max_age
        """
        db = TestingSessionLocal()
        test_user1 = User(name=TEST_USER_1_NAME, surname=TEST_USER_1_NAME,
                          age=TEST_USER_1_AGE)
        db.add(test_user1)
        test_user2 = User(name=TEST_USER_2_NAME, surname=TEST_USER_2_NAME,
                          age=TEST_USER_2_AGE)
        db.add(test_user2)
        test_user3 = User(name=TEST_USER_3_NAME, surname=TEST_USER_3_NAME,
                          age=TEST_USER_3_AGE)
        db.add(test_user3)
        db.commit()

        response = client.get("/users/")
        assert response.status_code == 200
        assert len(response.json()) == 3

        max_age = max(TEST_USER_1_AGE, TEST_USER_2_AGE, TEST_USER_3_AGE)
        response = client.get(f"/users/?max_age={max_age - 1}")
        assert response.status_code == 200
        assert len(response.json()) == 2

        min_age = min(TEST_USER_1_AGE, TEST_USER_2_AGE, TEST_USER_3_AGE)
        response = client.get(
            f"/users/?max_age={max_age - 1}&min_age={min_age + 1}")
        assert response.status_code == 200
        assert len(response.json()) == 1


class Test03Picnics:
    def test_get_picnics(self, test_db):
        """
        Проверка получения списка пикников
        """
        db = TestingSessionLocal()
        test_city = City(name=TEST_CITY_1_NAME)
        db.add(test_city)
        db.commit()

        picnic_time = dt.datetime.now()
        test_picnic = Picnic(city_id=test_city.id, time=picnic_time)
        db.add(test_picnic)
        db.commit()

        response = client.get("/picnics/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['city'] == TEST_CITY_1_NAME
        assert ans[0]['time'] == picnic_time.strftime(TIME_FORMAT)

    def test_create_picnic(self, test_db):
        """
        Проверка создания пикника
        """
        db = TestingSessionLocal()
        test_city = City(name=TEST_CITY_1_NAME)
        db.add(test_city)
        db.commit()

        picnic_time = dt.datetime.now().strftime(TIME_FORMAT)
        response = client.post(
            "/picnics/",
            json={"city_id": test_city.id, "datetime": picnic_time})
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 3
        assert ans['city'] == TEST_CITY_1_NAME
        assert ans['time'] == picnic_time

        response = client.get("/picnics/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['city'] == TEST_CITY_1_NAME
        assert ans[0]['time'] == picnic_time

    def test_search_picnic(self, test_db):
        """
        Проверка поска пикника по времени
        """
        db = TestingSessionLocal()
        test_city = City(name=TEST_CITY_1_NAME)
        db.add(test_city)
        db.commit()

        picnic_time1 = dt.datetime.now() - dt.timedelta(days=1)
        test_picnic1 = Picnic(city_id=test_city.id, time=picnic_time1)
        db.add(test_picnic1)
        picnic_time2 = dt.datetime.now() + dt.timedelta(days=1)
        test_picnic2 = Picnic(city_id=test_city.id, time=picnic_time2)
        db.add(test_picnic2)
        db.commit()

        response = client.get("/picnics/?past=False")
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = client.get(
            f"/picnics/?datetime={picnic_time2.strftime(TIME_FORMAT)}")
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = client.get(f"/picnics/?past=False&"
                              f"datetime={picnic_time1.strftime(TIME_FORMAT)}")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_picnic_reg(self, test_db):
        """
        Проверка регистрации на пикник
        """
        db = TestingSessionLocal()
        test_city = City(name=TEST_CITY_1_NAME)
        db.add(test_city)
        test_user = User(name=TEST_USER_1_NAME, surname=TEST_USER_1_NAME,
                         age=TEST_USER_1_AGE)
        db.add(test_user)
        db.commit()

        test_picnic = Picnic(city_id=test_city.id, time=dt.datetime.now())
        db.add(test_picnic)
        db.commit()

        response = client.post(
            "/picnic-register/",
            json={"user_id": test_user.id, "picnic_id": test_picnic.id})
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 3
        assert ans['picnic'] == test_picnic.id
        assert ans['user'] == test_user.name

        response = client.get("/picnics/")
        assert response.status_code == 200
        ans = response.json()
        assert len(ans) == 1
        assert ans[0]['city'] == test_city.name
        assert 'users' in ans[0]
        assert len(ans[0]['users']) == 1
        user = ans[0]['users'][0]
        assert user['id'] == test_user.id
        assert user['name'] == test_user.name
        assert user['surname'] == test_user.surname
        assert user['age'] == test_user.age
