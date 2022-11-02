import json

import phonenumbers
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order
from .models import OrderItem
from .models import Product


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })

def validate_order_datails(raw_order):
    verified_order = {}

    keys = ["products", "firstname", "lastname", "phonenumber", "address"]
    bad_fields = [key for key in keys if key not in raw_order]
    if bad_fields:
        return None, f"{', '.join(bad_fields)}: Обязательное поле."

    bad_fields = [key for key in keys if raw_order[key] is None]
    if bad_fields:
        return None, f"{', '.join(bad_fields)}: Это поле не может быть пустым."

    if not isinstance(raw_order["products"], list):
        return None, f"products: Ожидался list со значениями, но было получено {raw_order['products']}."
    
    if not raw_order["products"]:
        return None, "products: Этот список не может быть пустым."

    verified_order["products"] = []
    for product_details in raw_order["products"]:
        if not isinstance(product_details["quantity"], int):
            return None, f"quantity: Ожидалось значение типа int, но было получено {product_details['quantity']}."

        if product_details["quantity"] < 1:
            return None, f"quantity: Ожидалось положительное число, но было получено {product_details['quantity']}."

        if not isinstance(product_details["product"], int):
            return None, f"product: Ожидалось значение типа int, но было получено {product_details['product']}."

        if product_details["product"] < 1:
            return None, f"product: Ожидалось положительное число, но было получено {product_details['product']}."

        try:
            product = Product.objects.get(pk=product_details["product"])
        except Product.DoesNotExist:
            return None, 'products: Недопустимый первичный ключ ' "'" f'{product_details["product"]}' "'."

        verified_order["products"].append(
            {
                "product": product,
                "quantity": product_details["quantity"]
            }
        )

    keys = ["firstname", "lastname", "phonenumber", "address"]
    bad_fields = [key for key in keys if not isinstance(raw_order[key], str)]
    if bad_fields:
        return None, f"{', '.join(bad_fields)}: Not a valid string."

    firstname = raw_order["firstname"].strip()
    if not firstname:
        return None, "firstname: Эта строка не может быть пустой."

    verified_order["firstname"] = firstname

    lastname = raw_order["lastname"].strip()
    if not lastname:
        return None, "lastname: Эта строка не может быть пустой."

    verified_order["lastname"] = lastname

    phonenumber = raw_order["phonenumber"].strip()
    if not phonenumber:
        return None, "phonenumber: Эта строка не может быть пустой."

    phonenumber = phonenumbers.parse(phonenumber, 'RU')
    if not phonenumbers.is_valid_number(phonenumber):
        return None, "phonenumber: Введен некорректный номер телефона."

    verified_order["phonenumber"] = phonenumber

    address = raw_order["address"].strip()
    if not address:
        return None, "address: Эта строка не может быть пустой."

    verified_order["address"] = address
    return verified_order, None


@api_view(['POST'])
def register_order(request):
    raw_order = request.data

    verified_order, order_error = validate_order_datails(raw_order)
    if order_error:
        return Response({"error": order_error}, status=status.HTTP_406_NOT_ACCEPTABLE)

    order = Order.objects.create(
        firstname=verified_order["firstname"],
        lastname=verified_order["lastname"],
        phonenumber=verified_order["phonenumber"],
        address=verified_order["address"]
    )

    for product in verified_order["products"]:
        OrderItem.objects.create(order=order, product=product["product"], quantity=product["quantity"])

    return Response(raw_order, status=status.HTTP_200_OK)
