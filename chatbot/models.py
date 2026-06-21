from django.db import models

class Property(models.Model):
    project_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    price = models.IntegerField()
    size_sqft = models.IntegerField()

    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()

    floor = models.IntegerField()

    lift = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)

    balcony = models.IntegerField(default=0)

    def __str__(self):
        return self.project_name