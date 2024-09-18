# views.py
from rest_framework import generics, permissions, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from rest_framework import status
from .serializers import UserSerializer, UserProfileSerializer, MessageSerializer, ChatRoomSerializer, QuizSerializer, UserQuizDetailSerializer, UserQuizSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from .models import UserProfile, Message, ChatRoom, Quiz, UserQuiz
from django.db.models import Q, Max
from django.contrib.auth import get_user_model
from rest_framework.generics import RetrieveAPIView, UpdateAPIView

UserModel = get_user_model()

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Extract user data from request
        user_data = self.request.data
        username = user_data.get('username')
        email = user_data.get('email')
        mobile_num = user_data.get('mobile_num')
       
        # Check if the username, email, or mobile number already exists
        if User.objects.filter(username=username).exists():
            raise ValidationError({'username': 'A user with this Mobile Number already exists.'})

        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'A user with this email already exists.'})

        
        # Save the user and profile
        serializer.save()


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class ProfilePictureUpdateView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return self.update_profile_picture(request)

    def put(self, request, *args, **kwargs):
        return self.update_profile_picture(request)

    def update_profile_picture(self, request):
        if 'profile_pic' not in request.FILES:
            return Response({'detail': 'No profile picture uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Check if the profile already exists and has a picture
        if not created and profile.profile_pic:
            profile.profile_pic.delete(save=False)

        # Update the profile with the new picture
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        return UserProfile.objects.get(user=user)


class AdvisorsListAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_superuser=True).exclude(username='admin')
    
class UserDetailAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]  # Use AllowAny if public access is needed
    
    
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chat_room_and_send_message(request, receiver_id):
    sender = request.user
    content = request.data.get('content')

    # Check if content is provided
    if not content:
        return Response({'error': 'Message content is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve the receiver user from the receiver_id
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({'error': 'Receiver does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if a chat room already exists with these users
    existing_chat_rooms = ChatRoom.objects.filter(users=sender).filter(users=receiver)

    if existing_chat_rooms.exists():
        chat_room = existing_chat_rooms.first()
    else:
        # Create a new chat room and add both sender and receiver (you can add more users as needed)
        chat_room = ChatRoom.objects.create()
        chat_room.users.add(sender, receiver)

    # Create the message in the chat room
    message_data = {
        'chat_room': chat_room.id,
        'sender': sender.id,
        'content': content
    }
    message_serializer = MessageSerializer(data=message_data)

    if message_serializer.is_valid():
        message_serializer.save()
        return Response({
            'chat_room': ChatRoomSerializer(chat_room).data,
            'message': message_serializer.data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(message_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_rooms_for_logged_in_user(request):
    # Get the logged-in user
    user = request.user

    # Filter chat rooms where the logged-in user is a participant
    chat_rooms = ChatRoom.objects.filter(users=user)
    
    # Prepare data with the latest message
    data = []
    for room in chat_rooms:
        other_users = room.users.exclude(id=user.id)  # Exclude the current user
        latest_message = Message.objects.filter(chat_room=room).order_by('-timestamp').first()
        latest_message_content = latest_message.content if latest_message else "No messages yet"
        latest_message_timestamp = latest_message.timestamp if latest_message else None
        
        room_data = {
            'id': room.id,
            'other_users': [{'id': other_user.id, 'first_name': other_user.first_name, 'username': other_user.username} for other_user in other_users],
            'latest_message': latest_message_content,
            'timestamp': latest_message_timestamp
        }
        data.append(room_data)

    return Response(data, status=status.HTTP_200_OK)



class ChatRoomView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # Get both users from the URL parameters
        other_user_id = self.kwargs['other_user_id']
        current_user_id = self.kwargs['current_user_id']

        # Get the User objects for both users
        other_user = get_object_or_404(User, id=other_user_id)
        current_user = get_object_or_404(User, id=current_user_id)

        # Filter chat rooms that include both users
        chat_rooms = ChatRoom.objects.filter(users__in=[current_user, other_user]).distinct()

        # Further filter to ensure both users are in the chat room
        chat_rooms = [chat_room for chat_room in chat_rooms if 
                      chat_room.users.filter(id=current_user_id).exists() and
                      chat_room.users.filter(id=other_user_id).exists()]
        
        return chat_rooms

    def list(self, request, *args, **kwargs):
        chat_rooms = self.get_queryset()
        chat_room_data = []
        for chat_room in chat_rooms:
            # Serialize the chat room data
            chat_room_serializer = ChatRoomSerializer(chat_room)
            chat_room_id = chat_room_serializer.data['id']
            print(f"Chat Room ID: {chat_room_id}")  # Debugging line
            
            # Get messages for the chat room
            messages = Message.objects.filter(chat_room=chat_room_id).order_by('timestamp')
            print(f"Messages: {messages}")  # Debugging line
            
            message_serializer = MessageSerializer(messages, many=True)
            
            # Collect chat room info and messages
            chat_room_data.append({
                'chat_room_id': chat_room_id,
                'messages': message_serializer.data
            })

        return Response(chat_room_data, status=status.HTTP_200_OK)
    
    
class QuizCreateView(generics.CreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    def perform_create(self, serializer):
        # Assign the current user as the provider of the quiz
        serializer.save(provider=self.request.user)
        


class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.all()  # Fetch all quizzes
    serializer_class = QuizSerializer
    permission_classes = [AllowAny]
    

class QuizDetailView(RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    lookup_field = 'id'
    

class SubmitQuizAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already submitted an answer for this quiz
        if UserQuiz.objects.filter(user=request.user, quiz=quiz).exists():
            return Response({"error": "You have already submitted an answer for this quiz."}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare data with additional fields if necessary
        data = {
            'user': request.user.id,  # User ID
            'quiz': quiz.id,          # Quiz ID
            'answer': request.data.get('answer'),
            'status': request.data.get('status', False),
            'score': request.data.get('score', 0),
            'comment': request.data.get('comment', '')
        }

        serializer = UserQuizSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            user_quiz = serializer.save(user=request.user, quiz=quiz)
            return Response(UserQuizSerializer(user_quiz).data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)  # Log errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class CheckQuizStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        user_quiz = UserQuiz.objects.filter(user=request.user, quiz=quiz).first()

        if user_quiz:
            # Return the score, answer, and a message indicating the quiz has been taken
            return Response({
                "status": "already_taken",
                "score": user_quiz.score,
                "answer": user_quiz.answer  # Include the user's answer in the response
            }, status=status.HTTP_200_OK)
        
        # Return a response indicating that the quiz has not been taken
        return Response({
            "status": "not_taken",
            "score": 0,
            "answer": ""  # Send an empty answer if the quiz has not been taken
        }, status=status.HTTP_200_OK)
        
class QuizByProviderView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        provider_id = self.kwargs.get('provider_id')
        return Quiz.objects.filter(provider_id=provider_id)
    
class UserQuizListView(generics.ListAPIView):
    serializer_class = UserQuizDetailSerializer  # Use the new serializer

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        return UserQuiz.objects.filter(quiz_id=quiz_id, status="already_taken")


class UserQuizUpdateView(UpdateAPIView):
    queryset = UserQuiz.objects.all()
    serializer_class = UserQuizDetailSerializer

    def update(self, request, *args, **kwargs):
        # Get the UserQuiz object by ID
        user_quiz = self.get_object()

        # Update the score and comment
        serializer = self.get_serializer(user_quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)