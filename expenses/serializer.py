from rest_framework import serializers
from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['owner']


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()


    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['owner']