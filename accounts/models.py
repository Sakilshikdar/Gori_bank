from django.db import models
from django.contrib.auth.models import User
from .constants import ACCOUNT_TYPE, GENDER_TYPE


class UserBankAccount(models.Model):
    user = models.OneToOneField(
        User, related_name='account', on_delete=models.CASCADE)
    account_type = models.CharField(max_length=10,  choices=ACCOUNT_TYPE)
    account_no = models.IntegerField(unique=True)
    birth_date = models.DateField(null=True, blank=True)
    gender_type = models.CharField(max_length=10,  choices=GENDER_TYPE)
    initial_depositi_date = models.DateField(auto_now_add=True)
    balance = models.DecimalField(default=0, max_digits=12, decimal_places=2)

    def __str__(self):
        return str(self.account_no)


class UserAddress(models.Model):
    user = models.OneToOneField(
        User, related_name='address', on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    postal_code = models.IntegerField()

    def __str__(self):
        return self.user.email


class UserShareMoney(models.Model):
    account_id = models.IntegerField(unique=True)
    share_money = models.DecimalField(
        default=0, max_digits=12, decimal_places=2)

    def __str__(self):
        return self.user.email
