import requests
from django.conf import settings
from django.shortcuts import render

from .models import Location


def get_or_create_coordinates(address, locations):
    for location in locations:
        if location.address == address:
            return location.lat, location.lon

    lat, lon = fetch_coordinates_from_yandex_api(address)
    Location.objects.create(address=address, lat=lat, lon=lon)
    return lat, lon


def fetch_coordinates_from_yandex_api(address):
    base_url = 'https://geocode-maps.yandex.ru/1.x'
    response = requests.get(base_url, params={
        'geocode': address,
        'apikey': settings.YANDEX_GEO_API_KEY,
        'format': 'json',
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return 0, 0

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
    return lat, lon
