from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('adminworm/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('authapp.urls')),
]

handler404 = 'wormbooks.views.handler404'
handler500 = 'wormbooks.views.handler500'