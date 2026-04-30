from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect


def logout_view(request):
    auth_logout(request)
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)