# Ask user for their birthdate and zipcode of where they were born, and then tell them
# the weather for that location on their birthday.
# Then tell them the weather that happened on every subsequent birthday in that location.
# The user can also ask for the weather on a specific date.


import requests
import os
import sys
import re
from dateutil.parser import parse
from dotenv import load_dotenv
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

load_dotenv()

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)


def get_weather_data(lat, lng, date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lng,
        "start_date": date,
        "end_date": date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "daylight_duration", "sunshine_duration"],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/Chicago"
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()
    weather_data = {
        'temperature_max': daily.Variables(0).ValuesAsNumpy()[0],
        'temperature_min': daily.Variables(1).ValuesAsNumpy()[0],
        'temperature_mean': daily.Variables(2).ValuesAsNumpy()[0],
        'daylight_duration': daily.Variables(3).ValuesAsNumpy()[0],
        'sunshine_duration': daily.Variables(4).ValuesAsNumpy()[0]
    }
    return weather_data

# Get the Google Maps API key from the environment
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if GOOGLE_MAPS_API_KEY is None:
    print('You must set the GOOGLE_MAPS_API_KEY environment variable.')
    sys.exit(1)

# Get the user's birthdate
def get_birthdate():
    while True:
        birthdate = input('What is your birthdate? (YYYY-MM-DD) ')
        try:
            _ = parse(birthdate)
            return birthdate
        except ValueError:
            print('Please enter a valid date in the format YYYY-MM-DD.')

# Get the user's birth location
def get_birth_location():
    while True:
        birth_location = input('What is the zipcode of the place you were born? ')
        if re.match(r'^\d{5}$', birth_location):
            return birth_location
        else:
            print('Please enter a valid 5-digit zipcode.')
    
# Get the weather for a location on a specific date
def get_weather(location, date):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    data = response.json()
    lat = data['results'][0]['geometry']['location']['lat']
    lng = data['results'][0]['geometry']['location']['lng']
    weather_data = get_weather_data(lat, lng, date)
    return weather_data

if __name__ == "__main__":
    birthdate = get_birthdate()
    birth_location = get_birth_location()
    weather_data = get_weather(birth_location, birthdate)
    avg_temp = weather_data['temperature_mean']
    max_temp = weather_data['temperature_max']
    min_temp = weather_data['temperature_min']
    daylight_duration = weather_data['daylight_duration'] / 3600
    sunshine_duration = weather_data['sunshine_duration'] / 3600
    print(f'On your birthday {birthdate} in ZIP code {birth_location}:')
    print(f'Temperatures: -{min_temp:.2f}°F ={avg_temp:.2f}°F +{max_temp:.2f}°F')
    print(f'Daylight duration: {daylight_duration:.2f} hours')
    print(f'Sunshine duration: {sunshine_duration:.2f} hours')

