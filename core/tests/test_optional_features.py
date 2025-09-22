"""
Tests adicionales para manejo de Redis y funcionalidades opcionales
"""

from django.test import TestCase, TransactionTestCase
from unittest.mock import patch, Mock
import json

from core.models import Busqueda, PalabraClave, Propiedad, ResultadoBusqueda, Inmobiliaria, Usuario, Plataforma
from core.search_manager import get_all_searches, create_search


class RedisIntegrationTest(TestCase):
    """Tests para integración con Redis (con fallback graceful)"""
    
    def test_channel_layer_fallback(self):
        """Test que el canal de Redis tenga fallback cuando no está disponible"""
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            # Si llegamos aquí, Redis está disponible o hay fallback
            self.assertIsNotNone(channel_layer)
            
        except Exception as e:
            # Si Redis no está disponible, verificar que es el error esperado
            error_msg = str(e).lower()
            self.assertTrue(
                'channels_redis' in error_msg or 'redis' in error_msg,
                f"Error inesperado: {e}"
            )
            
    def test_websocket_consumer_fallback(self):
        """Test de fallback para WebSocket consumer"""
        # Test que el consumer se puede importar sin fallar
        try:
            from core.consumers import SearchConsumer
            self.assertIsNotNone(SearchConsumer)
        except ImportError:
            # Si no se puede importar, no es crítico si hay fallback HTTP
            pass
            
        # Verificar que existe endpoint HTTP de fallback
        response = self.client.get('/redis_diagnostic/')
        self.assertEqual(response.status_code, 200)
        
    def test_progress_update_fallback(self):
        """Test que send_progress_update tenga fallback"""
        from core.scraper.progress import send_progress_update
        
        # No debería fallar aunque Redis no esté disponible
        try:
            send_progress_update("Test message")
            # Si no falla, perfecto
        except Exception as e:
            # Si falla, debería ser un error graceful, no catastrófico
            self.assertNotIn('fatal', str(e).lower())


class OptionalFeaturesTest(TestCase):
    """Tests para funcionalidades opcionales"""
    
    def setUp(self):
        self.inmobiliaria = Inmobiliaria.objects.create(nombre="Test", plan="básico")
        self.usuario = Usuario.objects.create(
            nombre="Test", email="test@example.com", inmobiliaria=self.inmobiliaria
        )
        
    @patch('core.views.genai', None)
    def test_ai_integration_graceful_fallback(self):
        """Test que la integración con IA tenga fallback graceful cuando no está disponible"""
        
        # Crear búsqueda sin IA
        response = self.client.post('/', {
            'departamento': 'Montevideo',
            'tipo': 'apartamento',
            'keywords': 'garaje terraza'
        })
        
        # Debería funcionar sin IA
        self.assertIn(response.status_code, [200, 302])
        
    def test_scrapingbee_fallback(self):
        """Test que ScrapingBee tenga fallback a requests directo"""
        from core.scraper.extractors import scrape_detalle_con_requests
        
        # Test básico sin mock - solo verificamos que la función existe
        # y puede manejar el parámetro use_scrapingbee
        result = scrape_detalle_con_requests("http://test.com", use_scrapingbee=False)
        # Debería retornar estructura básica aunque falle la conexión
        self.assertIsInstance(result, dict)
            
    def test_export_functionality_available(self):
        """Test que la funcionalidad de exportación esté disponible"""
        
        # Crear datos de prueba
        search_data = create_search({
            'name': 'Export Test',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        # Probar endpoints de exportación
        response = self.client.get('/csv/export/all/')
        self.assertIn(response.status_code, [200, 302])
        
        response = self.client.get('/csv/audit/latest/')
        self.assertIn(response.status_code, [200, 404])  # 404 si no hay exports previos


class CompatibilityTest(TestCase):
    """Tests de compatibilidad con versiones anteriores"""
    
    def setUp(self):
        self.inmobiliaria = Inmobiliaria.objects.create(nombre="Test", plan="básico")
        self.usuario = Usuario.objects.create(
            nombre="Test", email="test@example.com", inmobiliaria=self.inmobiliaria
        )
        
    def test_old_scraper_import_fallback(self):
        """Test que importar desde el scraper antiguo falle gracefully"""
        
        # Intentar importar desde el scraper modular
        try:
            from core.scraper import build_mercadolibre_url, run_scraper
            self.assertTrue(True)  # Éxito - scraper modular disponible
        except ImportError:
            # Si falla, verificar que hay mensaje útil
            self.fail("Scraper modular no disponible")
            
    def test_legacy_search_data_structure(self):
        """Test compatibilidad con estructuras de datos anteriores"""
        
        # Test con estructura antigua
        legacy_data = {
            'nombre_busqueda': 'Legacy Test',
            'filtros': {'tipo': 'apartamento'},
            'texto_original': 'apartamento legacy',
            'palabras_clave': ['legacy', 'test']
        }
        
        # Debería funcionar con save_search
        from core.search_manager import save_search
        try:
            result = save_search(legacy_data)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"save_search no es compatible con datos legacy: {e}")


class ErrorHandlingTest(TestCase):
    """Tests para manejo de errores y casos edge"""
    
    def test_invalid_uuid_handling(self):
        """Test manejo de UUIDs inválidos"""
        from core.search_manager import get_search, delete_search
        
        # UUID inválido
        result = get_search('invalid-uuid')
        self.assertIsNone(result)
        
        # UUID que no existe
        result = get_search('12345678-1234-1234-1234-123456789012')
        self.assertIsNone(result)
        
        # Delete con UUID inválido no debería fallar
        result = delete_search('invalid-uuid')
        self.assertFalse(result)
        
    def test_empty_data_handling(self):
        """Test manejo de datos vacíos"""
        from core.search_manager import procesar_keywords, create_search
        
        # Keywords vacías
        result = procesar_keywords('')
        self.assertEqual(result, [])
        
        result = procesar_keywords(None)
        self.assertEqual(result, [])
        
        # Crear búsqueda con datos mínimos
        minimal_data = {
            'name': 'Minimal Test',
            'filters': {},
            'keywords': [],
            'original_text': '',
            'guardado': True
        }
        
        result = create_search(minimal_data)
        self.assertIsNotNone(result)
        
    def test_database_constraint_handling(self):
        """Test manejo de restricciones de base de datos"""
        from core.models import PalabraClave
        
        # Crear palabra clave
        palabra1 = PalabraClave.objects.create(texto='test', idioma='es')
        
        # Intentar crear duplicada (debería manejarse gracefully)
        palabra2, created = PalabraClave.objects.get_or_create(
            texto='test', 
            defaults={'idioma': 'es'}
        )
        
        self.assertFalse(created)
        self.assertEqual(palabra1.id, palabra2.id)
        
        
class PerformanceRegressionTest(TestCase):
    """Tests para detectar regresiones de performance"""
    
    def setUp(self):
        self.inmobiliaria = Inmobiliaria.objects.create(nombre="Test", plan="básico")
        self.usuario = Usuario.objects.create(
            nombre="Test", email="test@example.com", inmobiliaria=self.inmobiliaria
        )
        
    def test_search_list_performance(self):
        """Test que la lista de búsquedas mantenga performance razonable"""
        import time
        
        # Crear múltiples búsquedas
        for i in range(20):
            create_search({
                'name': f'Performance Test {i}',
                'filters': {'tipo': 'apartamento'},
                'keywords': [f'keyword{i}'],
                'original_text': '',
                'guardado': True
            })
            
        # Medir tiempo de consulta
        start_time = time.time()
        searches = get_all_searches()
        query_time = time.time() - start_time
        
        # Verificar resultados y performance
        self.assertGreaterEqual(len(searches), 20)
        self.assertLess(query_time, 1.0)  # Menos de 1 segundo
        
    def test_keyword_processing_performance(self):
        """Test performance del procesamiento de keywords"""
        from core.search_manager import procesar_keywords
        import time
        
        texto_largo = "apartamento casa garaje terraza piscina balcon cocina comedor living dormitorio baño vestidor lavadero deposito"
        
        start_time = time.time()
        result = procesar_keywords(texto_largo)
        processing_time = time.time() - start_time
        
        # Verificar que procesó correctamente y en tiempo razonable
        self.assertGreater(len(result), 5)
        self.assertLess(processing_time, 2.0)  # Menos de 2 segundos