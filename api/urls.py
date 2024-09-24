from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import ChatbotViewSet
# Create a router and register the ChatbotViewSet
api_router = DefaultRouter()
api_router.register(r'chatbot', ChatbotViewSet, basename='chatbot')

urlpatterns = [
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='get_token'),
    path('token/refresh', TokenRefreshView.as_view(), name='refresh_token'),
    
    
    path('user/', views.UserDetailView.as_view(), name='user_detail'),
    path('update-profile/', views.ProfilePictureUpdateView.as_view(), name='update-profile'),
    path('user-profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    
    path('advisors/', views.AdvisorsListAPIView.as_view(), name='advisors-list'),
    
    
    path('user/<int:id>/', views.UserDetailAPIView.as_view(), name='user-detail'),
    
    
    path('create-chat/<int:receiver_id>/', views.create_chat_room_and_send_message, name='create-chat'),
    path('my-chat-rooms/', views.get_chat_rooms_for_logged_in_user, name='my-chat-rooms'),
    path('chat_rooms/<int:other_user_id>/<int:current_user_id>/', views.ChatRoomView.as_view(), name='chat-room-list'),
    
    
    path('quizzes/create/', views.QuizCreateView.as_view(), name='quiz-create'),
    path('quizzes/', views.QuizListView.as_view(), name='quiz-list'),
    
    path('quiz/<int:id>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('submit-answer/<int:quiz_id>/', views.SubmitQuizAnswerView.as_view(), name='submit-quiz-answer'),
    path('check-quiz-status/<int:quiz_id>/', views.CheckQuizStatusView.as_view(), name='check-quiz-status'),
    
    path('quizzes/provider/<int:provider_id>/', views.QuizByProviderView.as_view(), name='quizzes-by-provider'),
    path('quizzes/<int:quiz_id>/users/', views.UserQuizListView.as_view(), name='user-quiz-list'),
    
    path('userquiz/<int:pk>/update/', views.UserQuizUpdateView.as_view(), name='userquiz-update'),
    
    path('', include(api_router.urls)),
]