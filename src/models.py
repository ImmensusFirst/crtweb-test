from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CityCreate(BaseModel):
    name: str = Field(description='Название города')


class CityBase(BaseModel):
    id: int
    name: str = Field(description='Название города')
    weather: str = Field(description='Погода в городе')

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str = Field(description='Имя пользователя')
    surname: str = Field(description='Фамилия пользователя')
    age: int = Field(description='Возраст')


class UserBase(BaseModel):
    id: int
    name: str = Field(description='Имя пользователя')
    surname: str = Field(description='Фамилия пользователя')
    age: int = Field(description='Возраст')

    class Config:
        orm_mode = True


class PicnicCreate(BaseModel):
    city_id: int = Field(description='ID города')
    datetime: datetime


class PicnicBase(BaseModel):
    id: int
    city: str = Field(description='Город для пикника')
    time: datetime = Field(description='Время проведения пикника')

    class Config:
        orm_mode = True


class PicnicList(PicnicBase):
    users: Optional[List[UserBase]] = None

    class Config:
        orm_mode = True


class PicnicReg(BaseModel):
    user_id: int = Field(description='ID пользователя')
    picnic_id: int = Field(description='ID пикника')


class PicnicResponse(BaseModel):
    id: int
    picnic: int = Field(description='ID пикника')
    user: str = Field(description='Имя пользователя')
