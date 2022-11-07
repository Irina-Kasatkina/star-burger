from django import forms
from django.contrib.auth import authenticate, login, views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from foodcartapp.models import Order, OrderItem, Product, Restaurant, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label="Логин",
        max_length=75,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Укажите имя пользователя"
            }
        )
    )
    password = forms.CharField(
        label="Пароль",
        max_length=75,
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите пароль"
            }
        )
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(
            request,
            "login.html",
            context={"form": form}
        )

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(
            request,
            "login.html",
            context={"form": form, "ivalid": True}
        )


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_products(request):
    restaurants = list(Restaurant.objects.order_by("name"))
    products = list(Product.objects.prefetch_related("menu_items"))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(
        request,
        template_name="products_list.html",
        context={
            "products_with_restaurant_availability": products_with_restaurant_availability,
            "restaurants": restaurants,
        }
    )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(
        request,
        template_name="restaurants_list.html",
        context={'restaurants': Restaurant.objects.all()}
    )


@user_passes_test(is_manager, login_url="restaurateur:login")
def view_orders(request):
    orders_items = OrderItem.objects.select_related("order", "product").exclude(order__status="CM").order_by("order__status", "order__id")
    restaurants_menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related("product", "restaurant")

    orders_for_page = []
    order = order_restaurants = None    
    for order_item in orders_items:
        if not order or order_item.order.id != order.id:
            if order:
                orders_for_page.append(serialize_order(order, order_cost, order_restaurants))

            order = order_item.order
            order_cost = order_item.price * order_item.quantity
            order_restaurants = get_order_item_restaurants(restaurants_menu_items, order_item)
            # print(order_restaurants)
        else:
            order_cost += order_item.price * order_item.quantity
            order_restaurants = order_restaurants & get_order_item_restaurants(restaurants_menu_items, order_item)

    if order:
        orders_for_page.append(serialize_order(order, order_cost, order_restaurants))
    # print(orders_for_page)

    return render(
        request,
        template_name="order_items.html",
        context={"orders": orders_for_page}
    )


def serialize_order(order, order_cost, restaurants_names):
    return {
        "id": order.id,
        "status": order.get_status_display(),
        "payment": order.get_payment_display(),
        "lastname": order.lastname,
        "firstname": order.firstname,
        "phonenumber": order.phonenumber,
        "address": order.address,
        "comment": order.comment,
        "cost": order_cost,
        "restaurant": order.restaurant.name if order.restaurant else "",
        "restaurants": sorted([restaurant_name for restaurant_name in restaurants_names])
    }


def get_order_item_restaurants(restaurants_menu_items, order_item):
    if order_item.order.restaurant:
        return set()

    return {
        restaurants_menu_item.restaurant.name
        for restaurants_menu_item in restaurants_menu_items
        if restaurants_menu_item.product.id == order_item.product.id
    }
