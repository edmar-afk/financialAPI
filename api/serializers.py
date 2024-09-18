from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Message, ChatRoom, Quiz, UserQuiz

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_pic']  # Include any other fields you want to expose
        extra_kwargs = {'profile_pic': {'required': False}}  # Make profile_pic optional

class UserSerializer(serializers.ModelSerializer):
    profile_pic = UserProfileSerializer(read_only=True)  # Nested serializer for UserProfile

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'password', 'date_joined', 'profile_pic', 'is_superuser']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user



class ChatRoomSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'users']  # Include 'users' field to show associated users

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())

    class Meta:
        model = Message
        fields = ['id', 'chat_room', 'sender', 'content', 'timestamp']
        

class QuizSerializer(serializers.ModelSerializer):
    provider = UserSerializer(read_only=True)  # Use UserSerializer for nested user representation

    class Meta:
        model = Quiz
        fields = ['id', 'provider', 'title', 'question', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            validated_data['provider'] = request.user  # Set the provider to the current logged-in user
        return Quiz.objects.create(**validated_data)
    
class UserQuizSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Read-only
    quiz = serializers.PrimaryKeyRelatedField(queryset=Quiz.objects.all())  # Accept quiz ID

    class Meta:
        model = UserQuiz
        fields = ['id', 'user', 'quiz', 'answer', 'status', 'score', 'created_at', 'comment']
        

class UserQuizDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nested UserDetailSerializer

    class Meta:
        model = UserQuiz
        fields = ['id', 'user', 'quiz', 'answer', 'status', 'score', 'created_at', 'comment']