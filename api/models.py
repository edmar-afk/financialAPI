from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_pic')
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

class ChatRoom(models.Model):
    users = models.ManyToManyField(User, related_name='chat_rooms')

    def __str__(self):
        return f'Chat Room with users: {", ".join(user.username for user in self.users.all())}'

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content}'


class Quiz(models.Model):
    provider = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=10000)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class UserQuiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='user_quiz')
    answer = models.TextField()
    status = models.TextField()
    score = models.IntegerField(default=0)  # Use IntegerField if score is numeric
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
   
    class Meta:
        unique_together = ('user', 'quiz')  # Ensure that a user can only take the same quiz once