from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8) # write_only without output password data
    password2 = serializers.CharField(write_only=True, min_length=8)


    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password2']


    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password': 'Password fields didn\'t match.'
            })
        
        return attrs
        
    
    def create(self, validated_data):
        return User.objects.create_user(
            email = validated_data['email'],
            username = validated_data['username'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            password = validated_data['password'],
        )