from django.db import models

# Create your models here.

class MarketPlace(models.Model):
    goods_name = models.CharField(max_length=50)
    goods_description = models.CharField(max_length=255)
    goods_quantity = models.CharField(max_length=50)
    any_offer = models.CharField(max_length=150)
    status = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.goods_name


