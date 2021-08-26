import datetime as dt

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from database import engine, Session, Base, City, User, Picnic, \
    PicnicRegistration
from external_requests import CheckCityExisting, GetWeatherRequest
from models import RegisterUserRequest, UserModel

app = FastAPI()


@app.get('/create-city/', summary='Create City',
         description='Создание города по его названию')
def create_city(city: str = Query(description="Название города", default=None)):
    if city is None:
        raise HTTPException(status_code=400,
                            detail='Параметр city должен быть указан')
    check = CheckCityExisting()
    if not check.check_existing(city):
        raise HTTPException(status_code=400,
                            detail='Параметр city должен быть существующим городом')

    city_object = Session().query(City).filter(
        City.name == city.capitalize()).first()
    if city_object is None:
        city_object = City(name=city.capitalize())
        s = Session()
        s.add(city_object)
        s.commit()

    return {'id': city_object.id, 'name': city_object.name,
            'weather': city_object.weather}


@app.post('/get-cities/', summary='Get Cities')
def cities_list(q: str = Query(description="Название города", default=None)):
    """
    Получение списка городов
    """
    if q is None:
        cities = Session().query(City).all()
    else:
        cities = Session().query(City).filter(City.name.startswith(q)).all()

    return [{'id': city.id, 'name': city.name, 'weather': city.weather} for city
            in cities]


@app.post('/users-list/', summary='')
def users_list(
        min_age: int = Query(description="Минимальный возраст", default=None),
        max_age: int = Query(description="Максимальный возраст", default=None)):
    """
    Список пользователей
    """
    q = Session().query(User)
    if min_age:
        q = q.filter(User.age >= min_age)
    if max_age:
        q = q.filter(User.age <= max_age)

    users = q.all()
    return [{
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'age': user.age,
    } for user in users]


@app.post('/register-user/', summary='CreateUser', response_model=UserModel)
def register_user(user: RegisterUserRequest):
    """
    Регистрация пользователя
    """
    user_object = User(**user.dict())
    s = Session()
    s.add(user_object)
    s.commit()

    return UserModel.from_orm(user_object)


@app.get('/all-picnics/', summary='All Picnics', tags=['picnic'])
def all_picnics(datetime: dt.datetime = Query(default=None,
                                              description='Время пикника (по умолчанию не задано)'),
                past: bool = Query(default=True,
                                   description='Включая уже прошедшие пикники')):
    """
    Список всех пикников
    """
    picnics = Session().query(Picnic)
    if datetime is not None:
        picnics = picnics.filter(Picnic.time == datetime)
    if not past:
        picnics = picnics.filter(Picnic.time >= dt.datetime.now())

    return [{
        'id': pic.id,
        'city': Session().query(City).filter(City.id == pic.id).first().name,
        'time': pic.time,
        'users': [
            {
                'id': pr.user.id,
                'name': pr.user.name,
                'surname': pr.user.surname,
                'age': pr.user.age,
            }
            for pr in Session().query(PicnicRegistration).filter(
                PicnicRegistration.picnic_id == pic.id)],
    } for pic in picnics]


@app.get('/picnic-add/', summary='Picnic Add', tags=['picnic'])
def picnic_add(city_id: int = None, datetime: dt.datetime = None):
    if city_id is None:
        raise HTTPException(status_code=400,
                            detail='Параметр city_id должен быть указан')
    if datetime is None:
        raise HTTPException(status_code=400,
                            detail='Параметр datetime должен быть указан')

    if not Session().query(
            Session().query(City).filter(City.id == city_id).exists()).scalar():
        raise HTTPException(status_code=404,
                            detail=f'Город city_id = {city_id} не найден!')

    p = Picnic(city_id=city_id, time=datetime)
    s = Session()
    s.add(p)
    s.commit()

    return {
        'id': p.id,
        'city': Session().query(City).filter(City.id == p.city_id).first().name,
        'time': p.time,
    }


@app.get('/picnic-register/', summary='Picnic Registration', tags=['picnic'])
def register_to_picnic(user_id: int = None, picnic_id: int = None):
    """
    Регистрация пользователя на пикник
    """

    if user_id is None:
        raise HTTPException(status_code=400,
                            detail='Параметр user_id должен быть указан')
    if picnic_id is None:
        raise HTTPException(status_code=400,
                            detail='Параметр picnic_id должен быть указан')

    if not Session().query(
            Session().query(Picnic).filter(
                Picnic.id == picnic_id).exists()).scalar():
        raise HTTPException(status_code=404,
                            detail=f'Пикник picnic_id = {picnic_id} не найден!')
    if not Session().query(
            Session().query(User).filter(
                User.id == user_id).exists()).scalar():
        raise HTTPException(status_code=404,
                            detail=f'Пользователь user_id = {user_id} не найден!')

    if Session().query(
            Session().query(PicnicRegistration).filter(
                PicnicRegistration.user_id == user_id,
                PicnicRegistration.picnic_id == picnic_id).exists()).scalar():
        raise HTTPException(status_code=400,
                            detail=f'Пользователь user_id = {user_id} уже '
                                   f'зарегистрирован на пикник {picnic_id}!')

    preg = PicnicRegistration(user_id=user_id, picnic_id=picnic_id)
    s = Session()
    s.add(preg)
    s.commit()

    return {
        'id': preg.id,
        'picnic': picnic_id,
        'user': Session().query(User).filter(
            User.id == preg.user_id).first().name,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
