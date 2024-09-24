# views.py
from rest_framework import generics, permissions, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from rest_framework import status, viewsets
from .serializers import UserSerializer, UserProfileSerializer, MessageSerializer, ChatRoomSerializer, ChatbotSerializer, QuizSerializer, UserQuizDetailSerializer, UserQuizSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from .models import UserProfile, Message, ChatRoom, Quiz, UserQuiz
from django.db.models import Q, Max
from django.contrib.auth import get_user_model
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
import json
from docx import Document
from sentence_transformers import SentenceTransformer, util
from django.views.decorators.csrf import csrf_exempt
UserModel = get_user_model()




import logging
import os
from typing import List, Optional
from rest_framework.response import Response
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
from pathlib import Path
from docx import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the relative path to the DOCX file
def get_docx_path() -> str:
    # Path to the DOCX file relative to this script
    return str(Path(__file__).parent / 'knowledge.docx')

def load_docx(file_path: str) -> str:
    try:
        full_path = file_path
        if not os.path.exists(full_path):
            logger.error(f"DOCX file does not exist at: {full_path}")
            return ""
        doc = Document(full_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        logger.info("DOCX loaded successfully.")
        return text
    except Exception as e:
        logger.error(f"Error loading DOCX: {e}")
        return ""

# Split the extracted text into chunks for easier searching
def split_text_into_chunks(text: str, chunk_size: int = 800) -> List[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode the text chunks
def encode_chunks(chunks: List[str]) -> List:
    return model.encode(chunks, convert_to_tensor=True)

# Find the best matching text chunk for a user question
def find_best_match_in_docx(user_question: str, text_chunks: List[str], threshold: float = 0.1) -> Optional[str]:
    user_question_embedding = model.encode(user_question, convert_to_tensor=True)
    chunk_embeddings = encode_chunks(text_chunks)
    similarities = util.pytorch_cos_sim(user_question_embedding, chunk_embeddings)
    
    logger.info(f"User question embedding: {user_question_embedding}")
    logger.info(f"Chunk embeddings: {chunk_embeddings}")
    logger.info(f"Similarities: {similarities}")

    # Get the index of the most similar chunk
    most_similar_idx = similarities.argmax()
    logger.info(f"Most similar index: {most_similar_idx}")
    logger.info(f"Highest similarity score: {similarities.max()}")

    # Check if the highest similarity chunk is a single paragraph
    answer = text_chunks[most_similar_idx] if similarities.max() > threshold else None

    if answer and '\n' not in answer:
        # Return the answer if it is a single paragraph
        return answer

    # Attempt to find a valid paragraph without new lines
    for idx, chunk in enumerate(text_chunks):
        if '\n' not in chunk and similarities[idx] > threshold:
            return chunk  # Return the first valid paragraph found

    return None  # No valid single paragraph found

class ChatbotViewSet(viewsets.ViewSet):
    serializer_class = ChatbotSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_question = serializer.validated_data['question']
            
            # Load and process the DOCX file
            docx_path = get_docx_path()  # Get the relative path
            docx_text = load_docx(docx_path)  # Use load_docx instead of load_pdf
            if not docx_text:
                return Response({'answer': "I don't understand the question."}, status=status.HTTP_200_OK)

            text_chunks = split_text_into_chunks(docx_text)
            logger.info(f"Text chunks: {text_chunks[:3]}")  # Log first few chunks for inspection

            # Find the best match in the DOCX text
            answer = find_best_match_in_docx(user_question, text_chunks)

            if answer:
                return Response({'answer': answer}, status=status.HTTP_200_OK)
            else:
                return Response({'answer': "I don't understand the question."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)











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

    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({'error': 'Receiver does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    existing_chat_rooms = ChatRoom.objects.filter(users=sender).filter(users=receiver)

    if existing_chat_rooms.exists():
        chat_room = existing_chat_rooms.first()
    else:
        chat_room = ChatRoom.objects.create()
        chat_room.users.add(sender, receiver)

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

    user = request.user

    chat_rooms = ChatRoom.objects.filter(users=user)
    
    data = []
    for room in chat_rooms:
        other_users = room.users.exclude(id=user.id)
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
        other_user_id = self.kwargs['other_user_id']
        current_user_id = self.kwargs['current_user_id']

        other_user = get_object_or_404(User, id=other_user_id)
        current_user = get_object_or_404(User, id=current_user_id)

        chat_rooms = ChatRoom.objects.filter(users__in=[current_user, other_user]).distinct()

        chat_rooms = [chat_room for chat_room in chat_rooms if 
                      chat_room.users.filter(id=current_user_id).exists() and
                      chat_room.users.filter(id=other_user_id).exists()]
        
        return chat_rooms

    def list(self, request, *args, **kwargs):
        chat_rooms = self.get_queryset()
        chat_room_data = []
        for chat_room in chat_rooms:
            chat_room_serializer = ChatRoomSerializer(chat_room)
            chat_room_id = chat_room_serializer.data['id']
            print(f"Chat Room ID: {chat_room_id}")
            
            # Get messages for the chat room
            messages = Message.objects.filter(chat_room=chat_room_id).order_by('timestamp')
            print(f"Messages: {messages}")
            
            message_serializer = MessageSerializer(messages, many=True)
            
            chat_room_data.append({
                'chat_room_id': chat_room_id,
                'messages': message_serializer.data
            })

        return Response(chat_room_data, status=status.HTTP_200_OK)
    
    
class QuizCreateView(generics.CreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)
        


class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.all() 
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

        if UserQuiz.objects.filter(user=request.user, quiz=quiz).exists():
            return Response({"error": "You have already submitted an answer for this quiz."}, status=status.HTTP_400_BAD_REQUEST)

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
            print("Serializer errors:", serializer.errors)
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
            return Response({
                "status": "already_taken",
                "score": user_quiz.score,
                "answer": user_quiz.answer,
                "comment": user_quiz.comment
            }, status=status.HTTP_200_OK)
            
        return Response({
            "status": "not_taken",
            "score": 0,
            "answer": "",
            "comment": ""
        }, status=status.HTTP_200_OK)
        
class QuizByProviderView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        provider_id = self.kwargs.get('provider_id')
        return Quiz.objects.filter(provider_id=provider_id)
    
class UserQuizListView(generics.ListAPIView):
    serializer_class = UserQuizDetailSerializer

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        return UserQuiz.objects.filter(quiz_id=quiz_id, status="already_taken")


class UserQuizUpdateView(UpdateAPIView):
    queryset = UserQuiz.objects.all()
    serializer_class = UserQuizDetailSerializer

    def update(self, request, *args, **kwargs):
        user_quiz = self.get_object()

        serializer = self.get_serializer(user_quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)