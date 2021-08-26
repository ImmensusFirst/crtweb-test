from pydantic import BaseModel


class CityCreate(BaseModel):
    name: str


class CityBase(BaseModel):
    id: int
    name: str
    weather: str

    class Config:
        orm_mode = True

class RegisterUserRequest(BaseModel):
    name: str
    surname: str
    age: int


class UserModel(BaseModel):
    id: int
    name: str
    surname: str
    age: int

    class Config:
        orm_mode = True
