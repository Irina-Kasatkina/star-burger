import requests
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Order, OrderItem, Product, Restaurant, RestaurantMenuItem
from geocoder.models import Location


class Login(forms.Form):
    username = forms.CharField(
        label='Логин',
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Укажите имя пользователя'
            }
        )
    )
    password = forms.CharField(
        label='Пароль',
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите пароль'
            }
        )
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(
            request,
            'login.html',
            context={'form': form}
        )

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect('restaurateur:RestaurantView')
                return redirect('start_page')

        return render(
            request,
            'login.html',
            context={'form': form, 'ivalid': True}
        )


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(
        request,
        template_name='products_list.html',
        context={
            'products_with_restaurant_availability': products_with_restaurant_availability,
            'restaurants': restaurants,
        }
    )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(
        request,
        template_name='restaurants_list.html',
        context={'restaurants': Restaurant.objects.all()}
    )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    restaurants_menu_items = (
        RestaurantMenuItem.objects
                          .filter(availability=True)
                          .prefetch_related('product', 'restaurant')
    )
    orders_items = (
        OrderItem.objects
                 .prefetch_related('order', 'product')
                 .exclude(order__status='CM')
                 .order_by('order__status', 'order__id')
    )

    locations = get_locations(restaurants_menu_items, orders_items)
    orders_for_page = generate_orders_for_page(restaurants_menu_items, orders_items, locations)

    return render(request, template_name='order_items.html', context={'orders': orders_for_page})


def generate_orders_for_page(restaurants_menu_items, orders_items, locations):
    orders_for_page = []
    order = order_restaurants = None

    for order_item in orders_items:
        if not order or order_item.order.id != order.id:
            if order:
                restaurants_definitions = get_restaurants_definitions(order.address, order_restaurants, locations)
                orders_for_page.append(serialize_order(order, order_cost, restaurants_definitions))

            order = order_item.order
            order_cost = order_item.price * order_item.quantity
            order_restaurants = get_order_item_restaurants(restaurants_menu_items, order_item)
        else:
            order_cost += order_item.price * order_item.quantity
            order_restaurants = order_restaurants & get_order_item_restaurants(restaurants_menu_items, order_item)

    if order:
        restaurants_definitions = get_restaurants_definitions(order.address, order_restaurants, locations)
        orders_for_page.append(serialize_order(order, order_cost, restaurants_definitions))

    return orders_for_page


def get_locations(restaurants_menu_items, orders_items):
    restaurants_addresses = {restaurant_menu_item.restaurant.address for restaurant_menu_item in restaurants_menu_items}
    orders_addresses = {order_item.order.address for order_item in orders_items}
    addresses = restaurants_addresses | orders_addresses
    return Location.objects.filter(address__in=addresses)


def get_restaurants_definitions(address, restaurants, locations):
    address_coordinates = get_or_create_coordinates(address, locations)

    restaurants_with_distances = []
    for restaurant in restaurants:
        restaurant_coordinates = get_or_create_coordinates(restaurant.address, locations)
        restaurant_distance = round(distance.distance(restaurant_coordinates, address_coordinates).km, 2)
        restaurants_with_distances.append((restaurant.name, restaurant_distance))

    restaurants_with_distances.sort(key=lambda x: x[1])
    return [
        f'{restaurant_name} - {restaurant_distance} км'
        for restaurant_name, restaurant_distance in restaurants_with_distances
    ]


def get_or_create_coordinates(address, locations):
    for location in locations:
        if location.address == address:
           return location.lat, location.lon

    lat, lon = fetch_coordinates_from_yandex_api(address)
    if lat and lon:
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
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
    return lat, lon


def serialize_order(order, order_cost, restaurants):
    return {
        'id': order.id,
        'status': order.get_status_display(),
        'payment': order.get_payment_display(),
        'lastname': order.lastname,
        'firstname': order.firstname,
        'phonenumber': order.phonenumber,
        'address': order.address,
        'comment': order.comment,
        'cost': order_cost,
        'restaurant': order.restaurant.name if order.restaurant else '',
        'restaurants': restaurants,
    }


def get_order_item_restaurants(restaurants_menu_items, order_item):
    if order_item.order.restaurant:
        return set()

    return {
        restaurants_menu_item.restaurant
        for restaurants_menu_item in restaurants_menu_items
        if restaurants_menu_item.product.id == order_item.product.id
    }
