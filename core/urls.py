# core/urls.py

from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('nueva/', views.nueva, name='nueva'),
    path('busqueda/<str:search_id>/', views.search_detail, name='search_detail'),
    path('eliminar/<str:search_id>/', views.delete_search, name='delete_search'),
    path('ajax/busqueda/<str:search_id>/', views.search_detail_ajax, name='search_detail_ajax'),
    path('detener_busqueda/', views.detener_busqueda_view, name='detener_busqueda'),
    path('ia_sugerir_filtros/', views.ia_sugerir_filtros, name='ia_sugerir_filtros'),
    path('http_search_fallback/', views.http_search_fallback, name='http_search_fallback'),
    path('redis_diagnostic/', views.redis_diagnostic, name='redis_diagnostic'),
    path('debug_screenshots/', views.debug_screenshots, name='debug_screenshots'),
    # CSV export endpoints
    path('csv/export/all/', views.csv_export_all, name='csv_export_all'),
    path('csv/table/<str:table>/', views.csv_export_table, name='csv_export_table'),
    path('csv/audit/latest/', views.csv_audit_latest, name='csv_audit_latest'),
]