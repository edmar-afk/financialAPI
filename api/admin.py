from django.contrib import admin
from .models import Message, ChatRoom, Quiz, UserQuiz
# Register your models here.


admin.site.register(Message)
admin.site.register(ChatRoom)
admin.site.register(Quiz)
admin.site.register(UserQuiz)