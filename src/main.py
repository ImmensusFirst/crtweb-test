import datetime as dt
from typing import List

from database import City, Picnic, PicnicRegistration, Session, User

from external_requests import CheckCityExisting

from fastapi import Depends
from fastapi import FastAPI, HTTPException, Query, status

from models import CityBase, CityCreate, PicnicBase, PicnicCreate, PicnicList
from models import PicnicReg, PicnicResponse, UserBase, UserCreate

import uvicorn

app = FastAPI()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.post('/cities/', summary='Create City',
          description='Создание города по его названию',
          tags=['cities'],
          response_model=CityBase)
def create_city(city: CityCreate, db: Session = Depends(get_db)):
    """
    Создание города
    """
    check = CheckCityExisting()
    if not check.check_existing(city.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Параметр city должен быть существующим '
                                   'городом')

    city_name = city.name.capitalize()
    city_object = db.query(City).filter(City.name == city_name).first()
    if city_object is None:
        city_object = City(name=city_name)
        db.add(city_object)
        db.commit()

    return CityBase.from_orm(city_object)


@app.get('/cities/', summary='Get Cities',
         description='Получение списка городов',
         tags=['cities'],
         response_model=List[CityBase], )
def cities_list(q: str = Query(description="Название города", default=None),
                db: Session = Depends(get_db)):
    """
    Получение списка городов
    """
    if q is None:
        cities = db.query(City).all()
    else:
        cities = db.query(City).filter(City.name.startswith(q)).all()
    return cities


@app.get('/users/', summary='Get Users',
         description='Получение списка пользователей',
         tags=['users'],
         response_model=List[UserBase], )
def users_list(
        min_age: int = Query(description="Минимальный возраст", default=None),
        max_age: int = Query(description="Максимальный возраст", default=None),
        db: Session = Depends(get_db)):
    """
    Получение списка пользователей
    """
    q = db.query(User)
    if min_age:
        q = q.filter(User.age >= min_age)
    if max_age:
        q = q.filter(User.age <= max_age)

    users = q.all()

    return users


@app.post('/users/', summary='Create User',
          description='Регистрация пользователя',
          tags=['users'],
          response_model=UserBase)
def user_create(user: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация пользователя
    """
    user_object = User(**user.dict())
    db.add(user_object)
    db.commit()

    return UserBase.from_orm(user_object)


@app.get('/picnics/', summary='Get Picnics',
         description='Получение списка пикников с зарег. пользователями',
         tags=['picnics'],
         response_model=List[PicnicList])
def picnics_list(datetime: dt.datetime =
                 Query(default=None,
                       description='Время пикника (по умолчанию не задано)'),
                 past: bool =
                 Query(default=True,
                       description='Включая уже прошедшие пикники'),
                 db: Session = Depends(get_db)):
    """
    Список всех пикников
    """
    picnics = db.query(Picnic, City)
    picnics = picnics.join(City, City.id == Picnic.city_id)

    if datetime is not None:
        picnics = picnics.filter(Picnic.time == datetime)
    if not past:
        picnics = picnics.filter(Picnic.time >= dt.datetime.now())

    output = [PicnicList(id=pic.id, city=city.name, time=pic.time,
                         users=[UserBase.from_orm(user) for _, user in
                                db.query(PicnicRegistration,
                                         User).filter(
                                    PicnicRegistration.picnic_id == pic.id)])
              for pic, city in picnics]
    return output


@app.post('/picnics/', summary='Create Picnic',
          description='Создание пикника',
          tags=['picnics'],
          response_model=PicnicBase)
def picnic_create(picnic: PicnicCreate, db: Session = Depends(get_db)):
    if not db.query(
            db.query(City).filter(
                City.id == picnic.city_id).exists()).scalar():
        raise HTTPException(status_code=404,
                            detail=f'Город city_id {picnic.city_id} '
                                   f'не найден!')

    p = Picnic(city_id=picnic.city_id, time=picnic.datetime)
    db.add(p)
    db.commit()

    return PicnicBase(id=p.id, city=db.query(City).filter(
        City.id == p.city_id).first().name, time=p.time)


@app.post('/picnic-register/', summary='Picnic Registration',
          description='Регистрация пользователя на пикник',
          tags=['picnics'],
          response_model=PicnicResponse)
def register_to_picnic(data: PicnicReg, db: Session = Depends(get_db)):
    """
    Регистрация пользователя на пикник
    """
    if not db.query(db.query(Picnic).filter(
            Picnic.id == data.picnic_id).exists()).scalar():
        raise HTTPException(status_code=404,
                            detail=f'Пикник {data.picnic_id} не найден!')
    if not db.query(db.query(User).filter(
            User.id == data.user_id).exists()).scalar():
        raise HTTPException(status_code=404,
                            detail=f'Пользователь {data.user_id} не найден!')

    if db.query(db.query(PicnicRegistration).filter(
            PicnicRegistration.user_id == data.user_id,
            PicnicRegistration.picnic_id == data.picnic_id).exists()).scalar():
        raise HTTPException(status_code=400,
                            detail=f'Пользователь user_id={data.user_id} уже '
                                   f'зарегистрирован на пикник '
                                   f'{data.picnic_id}!')

    preg = PicnicRegistration(user_id=data.user_id, picnic_id=data.picnic_id)
    db.add(preg)
    db.commit()

    return PicnicResponse(id=preg.id, picnic=data.picnic_id,
                          user=db.query(User).filter(
                              User.id == preg.user_id).first().name)


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
