from rest_framework import serializers

from .models import Repair


class TenantRequestRepairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    broken_property = serializers.CharField()
    description_broken_property = serializers.CharField()

class AllTenantRepairsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Repair
        fields = '__all__'