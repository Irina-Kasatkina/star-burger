from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
                              .filter(availability=True)
                              .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория товаров'
        verbose_name_plural = 'категории товаров'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('название', max_length=50)

    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField('картинка')

    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name='ресторан',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [['restaurant', 'product']]

    def __str__(self):
        return f'{self.restaurant.name} - {self.product.name}'


class Order(models.Model):
    """Заказ."""

    UNWATCHED = '1'
    COOKING = '2'
    DELIVERING = '3'
    COMPLETED = '4'
    ORDER_STATUSES = [
        (UNWATCHED, 'Необработанный'),
        (COOKING, 'Готовится'),
        (DELIVERING, 'Доставляется'),
        (COMPLETED, 'Выполнен'),
    ]

    CASH = 'CH'
    ONLINE = 'ON'
    PAYMENT_METHODS = [
        (CASH, 'Наличностью'),
        (ONLINE, 'Электронно'),
    ]

    status = models.CharField(
        'статус',
        max_length=2,
        choices=ORDER_STATUSES,
        default=UNWATCHED,
        db_index=True,
    )
    created = models.DateTimeField('время создания', auto_now_add=True, db_index=True)
    payment_method = models.CharField(
        'способ оплаты',
        max_length=2,
        choices=PAYMENT_METHODS,
        db_index=True,
    )
    call_datetime = models.DateTimeField('время звонка', null=True, blank=True, db_index=True)
    delivery_datetime = models.DateTimeField('время доставки', null=True, blank=True, db_index=True)
    firstname = models.CharField('имя', max_length=255)
    lastname = models.CharField('фамилия', max_length=255, db_index=True)
    phonenumber = PhoneNumberField('телефон', max_length=255, db_index=True)
    address = models.CharField('адрес', max_length=255)
    comment = models.TextField('комментарий', blank=True)

    cooking_restaurant = models.ForeignKey(
        Restaurant,
        related_name='orders',
        verbose_name='какой ресторан готовит',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.id}. {self.created} {self.firstname} {self.lastname}, телефон {self.phonenumber}'


class OrderItemQuerySet(models.QuerySet):
    def with_costs(self):
        return self.annotate(cost=F('price')*F('quantity'))


class OrderItem(models.Model):
    """Элемент заказа."""

    order = models.ForeignKey(
        Order,
        related_name='items',
        verbose_name='заказ',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        verbose_name='товар в заказе',
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField(
        'количество',
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(21)],
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    objects = OrderItemQuerySet.as_manager()

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'
