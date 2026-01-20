from django.contrib import admin
from .models import Category, Transaction


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['category', 'description', 'type', 'amount', 'date', 'owner']



admin.site.register(Category)
admin.site.register(Transaction, TransactionAdmin)
