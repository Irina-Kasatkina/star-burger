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


@api_view(['POST'])
def register_order(request):
    try:
        order_details = request.data
        print(request.data)

        phonenumber = order_details['phonenumber']
        phonenumber = phonenumbers.parse(phonenumber, 'RU')
        if not phonenumbers.is_valid_number(phonenumber):
            raise phonenumbers.NumberParseException

        products, quantities = [], []
        for product_details in order_details['products']:
            quantity = product_details['quantity']
            if quantity > 0:
                products.append(Product.objects.get(pk=product_details['product']))
                quantities.append(quantity)

        if not quantities:
            raise TypeError

        order = Order.objects.create(
            firstname=order_details['firstname'].strip().title(),
            lastname=order_details['lastname'].strip().title(),
            phonenumber=phonenumber,
            address=order_details['address'].strip()
        )

        for product, quantity in zip(products, quantities):
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

        print("Всё OK")
        return Response(order_details, status=status.HTTP_200_OK)

    except phonenumbers.NumberParseException:
        print('phonenumbers.NumberParseException')
        return Response({"error": "Неправильно заполнен номер телефона"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    except KeyError as error:
        field = str(error).strip("'")
        print('KeyError', error)
        return Response({"error": f"{field}: Обязательное поле."}, status=status.HTTP_406_NOT_ACCEPTABLE)

    except TypeError as error:
        print('TypeError', error)
        types = {
            str: "products: Ожидался list со значениями, но был получен 'str'",
            type(None): "products: Это поле не может быть пустым.",
            list: "products: Этот список не может быть пустым.",
        }
        message = types.get(type(order_details['products']), error)
        return Response({"error": message}, status=status.HTTP_406_NOT_ACCEPTABLE)

    except ValueError:
        print('ValueError', error)
        return Response({"error": "Неправильно заполнен заказ"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    return Response({}, status=status.HTTP_406_NOT_ACCEPTABLE)
