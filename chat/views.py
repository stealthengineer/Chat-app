from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils.text import slugify
from django.db.models import Count
from .models import Message, Room

def index(request):
    active_rooms = Room.objects.annotate(message_count=Count('messages')).order_by('-message_count')
    return render(request, 'chat/index.html', {
        'active_rooms': active_rooms,
        'user': request.user
    })

@login_required
def room(request, room_name):
    slug_room = slugify(room_name)

    # ✅ Get or create the Room instance using slug
    room, created = Room.objects.get_or_create(name=slug_room, defaults={'creator': request.user})

    if created:
        Message.objects.create(
            user=request.user,
            room=room,  # ✅ pass the actual Room object
            content=f"🚀 {request.user.username} created this room!"
        )

    messages = Message.objects.filter(room=room).order_by('timestamp')
    return render(request, 'chat/room.html', {
        'room_name': room.name,
        'username': request.user.username,
        'messages': messages,
        'can_delete': room.creator == request.user
    })

@login_required
def delete_room(request, room_name):
    room = get_object_or_404(Room, name=room_name)
    if request.user == room.creator:
        room.delete()
    return redirect('index')

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
