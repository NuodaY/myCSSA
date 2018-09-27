"""myCSSA URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import re_path, path, include
#from adminHub import views as adminHub
import adminHub, publicSite
from publicSite import views as homepage


urlpatterns = [
    # Url session for main site (全局入口)
    path('index/', homepage.index, name="Index"),
    path('adminhub/', include('adminHub.urls')),
    path('site/',include('publicSite.urls')),
    path('admin/', admin.site.urls),
    #re_path(r'^users/', include('django.contrib.auth.urls'))
    ]
