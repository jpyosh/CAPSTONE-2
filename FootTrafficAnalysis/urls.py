"""
URL configuration for FootTrafficAnalysis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib import messages

def index(request):
    return render(request, 'index.html', {'user': request.user})

def view(request):
    return render(request, 'viewdata.html')

def faq(request):
    return render(request, 'faq.html', {'user': request.user})

def loginUser(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Successfully logged in!')
            return redirect("/")
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def registerUser(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome aboard.')
            return redirect("/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def logoutUser(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect("/")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index),
    path("handleData/", include('databaseHandler.urls')),
    path("analyzeData/", include('dataAnalytics.urls')),
    path("login/", loginUser, name="loginPage"),
    path("register/", registerUser, name="registerPage"),
    path("logout/", logoutUser, name="logoutPage"),
    path("view/", view, name="view"),
    path("faq/", faq, name="faq"),
]