import requests

WEATHER_API_KEY = '99ba78ee79a2a24bc507362c5288a81b'


def get_weather_request(city):
    url = 'https://api.openweathermap.org/data/2.5/weather'
    url += '?units=metric'
    url += '&q=' + city
    url += '&appid=' + WEATHER_API_KEY

    response = requests.Session().get(url)
    if response.status_code != 200:
        return None
    else:
        data = response.json()
        return data['main']['temp']


def check_city_existing(city):
    return False if get_weather_request(city) is None else True
