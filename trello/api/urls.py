from django.urls import path
from django.urls import path, include, re_path
from trello.api import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('desk/', views.MainDeskListCreateView.as_view(), name='desk'),
    path('desk/<int:pk>', views.MainDeskDetail.as_view(), name='update-api-desk'),
    path('desk-archive/', views.MainDeskArchiveList.as_view()),
    path('column/<int:desk_pk>/<int:column_pk>/', views.ColumnDetail.as_view(), name='api-detail-column'),
    path('column/<int:desk_pk>/', views.ColumnListCreateView.as_view(), name='api-column'),
    path('card/<int:column_pk>/<int:card_pk>/', views.CardDetail.as_view(), name='api-detail-card'),
    path('card/<int:column_pk>/', views.CardListCreateView.as_view(), name='api-card'),
    path('comment/', views.CreateComment.as_view(), name='api-comment'),
    path('favourite/', views.FavouriteDetail.as_view()),
    path('invite/', views.SendInvite.as_view()),
    path('checklist/<int:pk>/', views.CheckListDetail.as_view()),
    path('checklist/', views.CheckListCreateView.as_view()),
    path('metki/<int:pk>/', views.MetkiDetail.as_view()),
    path('metki/list/<int:card_pk>/', views.MetkiCreateView.as_view()),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)