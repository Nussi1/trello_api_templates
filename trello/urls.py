from django.urls import path, include
from . import views


urlpatterns = [
	path('desk/', views.MainDeskView.as_view(), name='desks'),
	path('desk/add/', views.MainDeskCreateView.as_view(), name='desk-add'),
	path('desk/<int:pk>/update/', views.MainDeskUpdateView.as_view(), name='desk-update'),
	path('desk/<int:pk>/', views.MainDeskDetailView.as_view(), name='desk-detail'),
	path('desk/<int:pk>/delete/', views.MainDeskDeleteView.as_view(), name='desk-delete'),
	path('column/', views.ColumnView.as_view(), name='columns'),
	path('column/add/<int:pk>/', views.ColumnCreateView.as_view(), name='column-add'),
	path('column/<int:pk>/update/', views.ColumnUpdateView.as_view(), name='column-update'),
	path('column/<int:pk>/delete/', views.ColumnDeleteView.as_view(), name='column-delete'),
	path('column/<int:pk>/', views.ColumnDetailView.as_view(), name='column-detail'),
	path('card/', views.CardView.as_view(), name='cards'),
	path('card/add/<int:pk>/', views.CardCreateView.as_view(), name='card-add'),
	path('card/<int:pk>/update/', views.CardUpdateView.as_view(), name='card-update'),
	path('card/<int:pk>/delete/', views.CardDeleteView.as_view(), name='card-delete'),
	path('card/<int:pk>/', views.CardDetailView.as_view(), name='card-detail'),
	path("search", views.SearchView.as_view(), name="search"),
	path("desk/favourites", views.FavouriteListView.as_view(), name='favourites'),
	path("desk/favorites", include([
			path('', views.favorites_list, name='list'),
			path('<id>/add/', views.add_to_favorites, name='add'),
			path('<id>/remove/', views.remove_from_favorites, name='remove'),
			path('delete/', views.delete_favorites, name='delete'),
	])),
	path("desk/archives", views.ArchiveListView.as_view(), name='archives'),
	path("desk/archives", include([
			path('', views.archives_list, name='list_archive'),
			path('<id>/add/', views.add_to_archives, name='add_archive'),
			path('<id>/remove/', views.remove_from_archives, name='remove_archive'),
			path('delete/', views.delete_archives, name='delete_archive'),
	])),
	path('checklist/', views.CheckListView.as_view(), name='checklists'),
	path('checklist/add/<int:pk>/', views.CheckListCreateView.as_view(), name='checklist-add'),
	path('checklist/<int:pk>/update/', views.CheckListUpdateView.as_view(), name='checklist-update'),
	path('checklist/<int:pk>/delete/', views.CheckListDeleteView.as_view(), name='checklist-delete'),
	path('metki/', views.MetkiView.as_view(), name='metkis'),
	path('metki/add/<int:pk>/', views.MetkiCreateView.as_view(), name='metki-add'),
	path('metki/<int:pk>/update/', views.MetkiUpdateView.as_view(), name='metki-update'),
	path('metki/<int:pk>/delete/', views.MetkiDeleteView.as_view(), name='metki-delete'),
]