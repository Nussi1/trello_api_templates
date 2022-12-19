from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('', TemplateView.as_view(template_name='base_board.html')),
    path('admin/', admin.site.urls),
    path('trello/', include('trello.urls')),
    path('api/', include('trello.api.urls')),
    path('api-auth', include('rest_framework.urls', namespace='rest_framework')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
