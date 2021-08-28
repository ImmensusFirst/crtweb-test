import os

from external_requests import get_weather_request

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, \
    create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Создание сессии
DATABASE_HOST = os.environ.get('DATABASE_HOST', None)

if DATABASE_HOST:
    DATABASE_HOST = os.environ.get('DATABASE_HOST', None)
    DATABASE_PORT = os.environ.get('DATABASE_PORT', None)
    DATABASE_NAME = os.environ.get('DATABASE_NAME', None)
    DATABASE_USER = os.environ.get('DATABASE_USER', None)
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', None)
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DATABASE_USER}:' \
                              f'{DATABASE_PASSWORD}@' \
                              f'{DATABASE_HOST}/{DATABASE_NAME}'
else:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///./main.db'

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Подключение базы (с автоматической генерацией моделей)
Base = declarative_base()


class City(Base):
    """
    Город
    """
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    @property
    def weather(self) -> str:
        """
        Возвращает текущую погоду в этом городе
        """
        return get_weather_request(self.name)

    def __repr__(self):
        return f'<Город "{self.name}">'


class User(Base):
    """
    Пользователь
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    age = Column(Integer, nullable=True)

    def __repr__(self):
        return f'<Пользователь {self.surname} {self.name}>'


class Picnic(Base):
    """
    Пикник
    """
    __tablename__ = 'picnic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, ForeignKey('city.id'), nullable=False)
    time = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'<Пикник {self.id}>'


class PicnicRegistration(Base):
    """
    Регистрация пользователя на пикник
    """
    __tablename__ = 'picnic_registration'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    picnic_id = Column(Integer, ForeignKey('picnic.id'), nullable=False)

    user = relationship('User', backref='picnics')
    picnic = relationship('Picnic', backref='users')

    def __repr__(self):
        return f'<Регистрация {self.id}>'


Base.metadata.create_all(bind=engine)
