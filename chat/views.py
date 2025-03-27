from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Message
from django.db.models import Count

# 👇 Shows homepage whether user is logged in or not
def index(request):
    return render(request, 'chat/index.html')

# 👇 Protected: only logged-in users can enter chat rooms
@login_required
def room(request, room_name):
    messages = Message.objects.filter(room=room_name).order_by('timestamp')
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'username': request.user.username,
        'messages': messages
    })

# 👇 User signup view
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'chat/signup.html', {'form': form})

def index(request):
    active_rooms = Message.objects.values('room') \
        .annotate(message_count=Count('id')) \
        .order_by('-message_count')

    return render(request, 'chat/index.html', {
        'active_rooms': active_rooms
    })
