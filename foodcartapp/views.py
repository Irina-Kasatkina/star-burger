import json

import phonenumbers
from django.http import JsonResponse
from django.templatetags.static import static

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


def register_order(request):
    try:
        order_details = json.loads(request.body.decode())

        phonenumber = order_details['phonenumber']
        phonenumber = phonenumbers.parse(phonenumber, 'RU')
        if not phonenumbers.is_valid_number(phonenumber):
            raise phonenumbers.NumberParseException

        order = Order.objects.create(
            firstname=order_details['firstname'].strip().title(),
            lastname=order_details['lastname'].strip().title(),
            phonenumber=phonenumber,
            address=order_details['address'].strip()
        )
        for product_details in order_details['products']:
            quantity = product_details['product']
            if quantity > 0:
                product = Product.objects.get(pk=product_details['product'])
                OrderItem.objects.create(order=order, product=product, quantity=quantity)
    except ValueError:
        return JsonResponse({'error': 'Неправильно заполнен заказ'})
    except phonenumbers.NumberParseException:
        return JsonResponse({'error': 'Неправильно заполнен номер телефона'})
    return JsonResponse({})
