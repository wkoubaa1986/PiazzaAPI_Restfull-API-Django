from rest_framework import serializers
from .models import Preference

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields=('id','owner','post','value','created_on','time_to_expire')