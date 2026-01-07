from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category, Transaction
from .serializer import CategorySerializer, TransactionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)
    

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)
    

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)