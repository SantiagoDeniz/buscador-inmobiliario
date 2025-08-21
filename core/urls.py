# core/urls.py

from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('busqueda/<str:search_id>/', views.search_detail, name='search_detail'),
    path('eliminar/<str:search_id>/', views.delete_search, name='delete_search'),
    path('ajax/busqueda/<str:search_id>/', views.search_detail_ajax, name='search_detail_ajax'),
    path('detener_busqueda/', views.detener_busqueda_view, name='detener_busqueda'),
    path('ia_sugerir_filtros/', views.ia_sugerir_filtros, name='ia_sugerir_filtros'),
]