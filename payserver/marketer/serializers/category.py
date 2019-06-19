from rest_framework import serializers
from common.models import MerchantCategory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantCategory
        fields = ('name',)


class NestedCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantCategory
        fields = ('name', 'parent')

    parent = CategorySerializer()