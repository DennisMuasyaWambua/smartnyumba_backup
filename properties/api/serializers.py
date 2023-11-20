from rest_framework import serializers

class AddPropertySerializer(serializers.Serializer):
    location = serializers.CharField()
    block_number = serializers.CharField()
    block_landlord_email = serializers.EmailField()

class AddBlockHousesSerializer(serializers.Serializer):
    house_number = serializers.CharField()
    block = serializers.CharField()
    service_charge = serializers.DecimalField(decimal_places=2, max_digits=5)
    rent_charged = serializers.DecimalField(decimal_places=2, max_digits=10)

