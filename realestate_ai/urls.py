from django.contrib import admin
from django.urls import path
from chatbot.views import chat_page, chat_response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', chat_page),         
    path('chat/', chat_response), 
]