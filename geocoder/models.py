from django.db import models


class Location(models.Model):
    verified_at = models.DateField('дата запроса к геокодеру', auto_now_add=True, db_index=True)
    address = models.CharField('адрес', max_length=255, db_index=True, unique=True)
    lat = models.FloatField('широта', null=False)
    lon = models.FloatField('долгота', null=False)

    class Meta:
        verbose_name = 'локация'
        verbose_name_plural = 'локации'

    def __str__(self):
        return f'{self.address} : lat={self.lat} lon={self.lon}'