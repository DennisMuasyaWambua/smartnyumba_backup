from django.db import models

# Create your models here.


class Repair(models.Model):
    email = models.EmailField()
    broken_property = models.CharField(max_length=50)
    description_broken_property = models.TextField()

    class Meta:
        db_table = 'repairs'
        verbose_name_plural = 'repairs'

    def __str__(self):
        return self.email