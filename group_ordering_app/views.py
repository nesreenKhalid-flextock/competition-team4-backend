
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Welcome to Group Ordering App!</h1><p>Your Django app is running successfully on Replit.</p>")
