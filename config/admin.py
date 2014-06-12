from django.contrib import admin
from models import UserConfig, CompanyConfig
from pos.models import Country

admin.site.register(UserConfig)
admin.site.register(CompanyConfig)

admin.site.register(Country)

