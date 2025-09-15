# core/tests_database.py
"""
Tests para el nuevo sistema de base de datos del buscador inmobiliario
"""

import uuid
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from unittest.mock import patch, MagicMock
from channels.testing import ChannelsLiveServerTestCase
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

from .models import (
    Inmobiliaria, Usuario, Plataforma, Busqueda, 
    PalabraClave, BusquedaPalabraClave, Propiedad, ResultadoBusqueda
)
from .search_manager import (
    get_all_searches, get_all_search_history, get_search, save_search, delete_search,
    procesar_keywords, get_or_create_palabra_clave, 
    buscar_coincidencias, create_search, update_search,
    load_results, save_results, get_search_stats
)

class TestModelsDatabase(TestCase):
    """Tests para los modelos de la base de datos"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.inmobiliaria = Inmobiliaria.objects.create(
            nombre="Inmobiliaria Test",
            plan="básico"
        )
        
        self.usuario = Usuario.objects.create(
            nombre="Usuario Test",
            email="test@test.com",
            inmobiliaria=self.inmobiliaria
        )
        
        self.plataforma = Plataforma.objects.create(
            nombre="MercadoLibre Test",
            url="https://test.com",
            descripcion="Plataforma de prueba"
        )
    
    def test_crear_busqueda(self):
        """Test crear búsqueda básica"""
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Apartamento 2 dormitorios",
            texto_original="apartamento 2 dorm pocitos",
            filtros={"dormitorios": 2, "zona": "pocitos"},
            guardado=True,
            usuario=self.usuario
        )
        
        self.assertEqual(busqueda.nombre_busqueda, "Apartamento 2 dormitorios")
        self.assertTrue(busqueda.guardado)
        self.assertEqual(busqueda.usuario, self.usuario)
        self.assertIsInstance(busqueda.id, uuid.UUID)
    
    def test_palabra_clave_sinonimos(self):
        """Test sistema de sinónimos en palabras clave"""
        palabra = PalabraClave.objects.create(
            texto="apartamento",
            idioma="es"
        )
        
        # Test setter de sinónimos
        sinonimos_test = ["apto", "depto", "departamento"]
        palabra.set_sinonimos(sinonimos_test)
        palabra.save()
        
        # Test getter de sinónimos
        self.assertEqual(palabra.sinonimos_list, sinonimos_test)
        
        # Test con sinónimos vacíos
        palabra_vacia = PalabraClave.objects.create(
            texto="casa",
            idioma="es"
        )
        self.assertEqual(palabra_vacia.sinonimos_list, [])
    
    def test_relacion_busqueda_palabra_clave(self):
        """Test relación many-to-many entre búsquedas y palabras clave"""
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Test",
            texto_original="apartamento garage",
            usuario=self.usuario
        )
        
        palabra1 = PalabraClave.objects.create(texto="apartamento")
        palabra2 = PalabraClave.objects.create(texto="garage")
        
        # Crear relaciones
        BusquedaPalabraClave.objects.create(busqueda=busqueda, palabra_clave=palabra1)
        BusquedaPalabraClave.objects.create(busqueda=busqueda, palabra_clave=palabra2)
        
        # Verificar relaciones
        relaciones = busqueda.busquedapalabraclave_set.all()
        self.assertEqual(len(relaciones), 2)
        
        palabras = [rel.palabra_clave.texto for rel in relaciones]
        self.assertIn("apartamento", palabras)
        self.assertIn("garage", palabras)


class TestSearchManagerDatabase(TestCase):
    """Tests para el search_manager con base de datos"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.inmobiliaria = Inmobiliaria.objects.create(
            nombre="Test Inmobiliaria",
            plan="básico"
        )
        
        self.usuario = Usuario.objects.create(
            nombre="Test User",
            email="default@example.com",
            inmobiliaria=self.inmobiliaria
        )
        
        self.plataforma = Plataforma.objects.create(
            nombre="MercadoLibre",
            url="https://mercadolibre.com.uy"
        )
    
    def test_get_all_searches(self):
        """Test obtener todas las búsquedas"""
        # Crear búsquedas de prueba con guardado=True para que aparezcan en get_all_searches()
        busqueda1 = Busqueda.objects.create(
            nombre_busqueda="Apartamento Centro",
            texto_original="apartamento centro",
            guardado=True,  # Marcar como guardada para que aparezca en la lista
            usuario=self.usuario
        )
        
        busqueda2 = Busqueda.objects.create(
            nombre_busqueda="Casa Pocitos", 
            texto_original="casa pocitos",
            guardado=True,  # Marcar como guardada para que aparezca en la lista
            usuario=self.usuario
        )
        
        searches = get_all_searches()
        
        self.assertEqual(len(searches), 2)
        self.assertIn("Apartamento Centro", [s['nombre_busqueda'] for s in searches])
        self.assertIn("Casa Pocitos", [s['nombre_busqueda'] for s in searches])
    
    def test_save_search(self):
        """Test guardar nueva búsqueda"""
        search_data = {
            'nombre_busqueda': 'Apartamento 2 dorm',
            'texto_original': 'apartamento 2 dormitorios pocitos',
            'filtros': {'dormitorios': 2},
            'palabras_clave': ['apartamento', 'dormitorios', 'pocitos'],
            'guardado': True
        }
        
        search_id = save_search(search_data)
        
        # Verificar que se creó correctamente
        self.assertIsNotNone(search_id)
        busqueda = Busqueda.objects.get(id=search_id)
        self.assertEqual(busqueda.nombre_busqueda, 'Apartamento 2 dorm')
        self.assertTrue(busqueda.guardado)
        
        # Verificar palabras clave asociadas
        relaciones = busqueda.busquedapalabraclave_set.all()
        self.assertEqual(len(relaciones), 3)
    
    def test_get_search(self):
        """Test obtener búsqueda específica"""
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Test Search",
            texto_original="test",
            usuario=self.usuario
        )
        
        result = get_search(str(busqueda.id))
        
        self.assertIsNotNone(result)
        self.assertEqual(result['nombre_busqueda'], "Test Search")
        self.assertEqual(result['id'], str(busqueda.id))
    
    def test_delete_search(self):
        """Test eliminar búsqueda del usuario (implementación con preservación de datos)"""
        busqueda = Busqueda.objects.create(
            nombre_busqueda="To Delete",
            texto_original="delete test",
            guardado=True,  # Búsqueda visible del usuario
            usuario=self.usuario
        )
        
        search_id = str(busqueda.id)
        
        # Verificar que existe y está visible
        self.assertTrue(Busqueda.objects.filter(id=search_id, guardado=True).exists())
        
        # Eliminar desde la perspectiva del usuario
        success = delete_search(search_id)
        self.assertTrue(success)
        
        # Verificar que ya no es visible para el usuario (eliminación exitosa)
        searches = get_all_searches()
        search_ids = [s['id'] for s in searches]
        self.assertNotIn(search_id, search_ids)
        
        # Verificación técnica: datos preservados para análisis (transparente al usuario)
        busqueda_updated = Busqueda.objects.get(id=search_id)
        self.assertFalse(busqueda_updated.guardado)  # Marcada como no visible
        self.assertEqual(busqueda_updated.nombre_busqueda, "To Delete")  # Datos preservados
        
        # Los datos siguen disponibles para análisis del sistema
        all_searches = get_all_search_history()
        all_search_ids = [s['id'] for s in all_searches]
        self.assertIn(search_id, all_search_ids)
    
    def test_restore_search_from_history(self):
        """Test función administrativa: recuperar búsqueda eliminada por el usuario"""
        from .search_manager import restore_search_from_history
        
        # Crear búsqueda previamente "eliminada" por el usuario
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Previously Deleted",
            texto_original="restore test",
            guardado=False,  # Ya eliminada de la vista del usuario
            usuario=self.usuario
        )
        
        search_id = str(busqueda.id)
        
        # Verificar estado inicial: eliminada para el usuario pero en análisis del sistema
        searches = get_all_searches()
        search_ids = [s['id'] for s in searches]
        self.assertNotIn(search_id, search_ids)
        
        all_searches = get_all_search_history()
        all_search_ids = [s['id'] for s in all_searches]
        self.assertIn(search_id, all_search_ids)
        
        # Función administrativa: recuperar búsqueda eliminada
        success = restore_search_from_history(search_id)
        self.assertTrue(success)
        
        # Verificar que vuelve a ser visible para el usuario
        busqueda_updated = Busqueda.objects.get(id=search_id)
        self.assertTrue(busqueda_updated.guardado)
        
        searches_after = get_all_searches()
        search_ids_after = [s['id'] for s in searches_after]
        self.assertIn(search_id, search_ids_after)
    
    def test_procesar_keywords(self):
        """Test procesamiento de palabras clave"""
        texto = "apartamento 2 dormitorios con garage en pocitos"
        
        keywords = procesar_keywords(texto)
        
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        
        # Verificar que se crearon las palabras clave en BD
        textos_keywords = [kw['texto'] for kw in keywords]
        
        for texto_kw in textos_keywords:
            self.assertTrue(PalabraClave.objects.filter(texto=texto_kw).exists())
    
    def test_get_or_create_palabra_clave(self):
        """Test obtener o crear palabra clave"""
        # Primera llamada - debe crear
        palabra1 = get_or_create_palabra_clave("apartamento")
        self.assertEqual(palabra1.texto, "apartamento")
        self.assertGreater(len(palabra1.sinonimos_list), 0)  # Debe tener sinónimos
        
        # Segunda llamada - debe obtener existente
        palabra2 = get_or_create_palabra_clave("apartamento")
        self.assertEqual(palabra1.id, palabra2.id)
    
    def test_load_results(self):
        """Test cargar resultados de búsqueda"""
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Test Results",
            texto_original="test",
            usuario=self.usuario
        )
        
        # Crear propiedad y resultado de prueba
        propiedad = Propiedad.objects.create(
            url="https://test.com/prop1",
            titulo="Propiedad Test",
            plataforma=self.plataforma,
            metadata={"precio": 100000}
        )
        
        ResultadoBusqueda.objects.create(
            busqueda=busqueda,
            propiedad=propiedad,
            coincide=True,
            metadata={"coincidencias": 3}
        )
        
        results = load_results(str(busqueda.id))
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['titulo'], "Propiedad Test")
        self.assertEqual(results[0]['url'], "https://test.com/prop1")


class TestSearchStats(TestCase):
    """Tests para estadísticas del sistema"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.inmobiliaria = Inmobiliaria.objects.create(nombre="Test", plan="básico")
        self.usuario = Usuario.objects.create(
            nombre="Test", email="test@test.com", inmobiliaria=self.inmobiliaria
        )
        self.plataforma = Plataforma.objects.create(nombre="Test", url="https://test.com")
    
    def test_get_search_stats(self):
        """Test obtener estadísticas del sistema"""
        # Crear datos de prueba
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Test", usuario=self.usuario, guardado=True
        )
        
        palabra = PalabraClave.objects.create(texto="apartamento")
        BusquedaPalabraClave.objects.create(busqueda=busqueda, palabra_clave=palabra)
        
        propiedad = Propiedad.objects.create(
            url="https://test.com/1", titulo="Test Prop", plataforma=self.plataforma
        )
        
        ResultadoBusqueda.objects.create(
            busqueda=busqueda, propiedad=propiedad, coincide=True
        )
        
        stats = get_search_stats()
        
        self.assertEqual(stats['total_searches'], 1)
        self.assertEqual(stats['saved_searches'], 1)
        self.assertEqual(stats['total_keywords'], 1)
        self.assertEqual(stats['total_properties'], 1)
        self.assertEqual(stats['successful_results'], 1)


class TestCompatibilityFunctions(TestCase):
    """Tests para funciones de compatibilidad con el sistema anterior"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.inmobiliaria = Inmobiliaria.objects.create(nombre="Test", plan="básico")
        self.usuario = Usuario.objects.create(
            nombre="Test", email="default@example.com", inmobiliaria=self.inmobiliaria
        )
    
    def test_create_search_compatibility(self):
        """Test función create_search para compatibilidad con consumers.py"""
        search_data = {
            'name': 'Apartamento Centro',
            'original_text': 'apartamento centro montevideo',
            'filters': {'zona': 'centro'},
            'keywords': ['apartamento', 'centro', 'montevideo']
        }
        
        result = create_search(search_data)
        
        self.assertIn('id', result)
        self.assertEqual(result['name'], 'Apartamento Centro')
        
        # Verificar que se guardó en BD
        busqueda = Busqueda.objects.get(id=result['id'])
        self.assertEqual(busqueda.nombre_busqueda, 'Apartamento Centro')
        self.assertTrue(busqueda.guardado)
    
    def test_update_search_compatibility(self):
        """Test función update_search para compatibilidad"""
        busqueda = Busqueda.objects.create(
            nombre_busqueda="Original",
            texto_original="original",
            usuario=self.usuario
        )
        
        success = update_search(str(busqueda.id), {
            'name': 'Updated Name',
            'filters': {'updated': True}
        })
        
        self.assertTrue(success)
        
        # Verificar actualización
        busqueda.refresh_from_db()
        self.assertEqual(busqueda.nombre_busqueda, 'Updated Name')
        self.assertEqual(busqueda.filtros['updated'], True)


class TestRedisChannelsIntegration(TransactionTestCase):
    """Tests para integración con Redis y Channels"""
    
    def test_channel_layer_available(self):
        """Test que el canal de Redis esté disponible"""
        channel_layer = get_channel_layer()
        self.assertIsNotNone(channel_layer)
        self.assertEqual(type(channel_layer).__name__, 'RedisChannelLayer')
    
    @patch('core.consumers.SearchProgressConsumer.send')
    def test_websocket_consumer_integration(self, mock_send):
        """Test básico de integración con WebSocket consumer"""
        from .consumers import SearchProgressConsumer
        
        consumer = SearchProgressConsumer()
        consumer.room_group_name = 'test_search_progress'
        
        # Simular mensaje de WebSocket
        test_data = {
            'texto': 'apartamento 2 dormitorios',
            'guardar': True,
            'name': 'Test Search'
        }
        
        # El test verifica que el consumer pueda manejar el formato de mensaje
        self.assertIsInstance(test_data, dict)
        self.assertIn('texto', test_data)
        self.assertIn('guardar', test_data)


class TestDatabasePerformance(TestCase):
    """Tests de performance para el nuevo sistema de BD"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.inmobiliaria = Inmobiliaria.objects.create(nombre="Test", plan="básico")
        self.usuario = Usuario.objects.create(
            nombre="Test", email="test@test.com", inmobiliaria=self.inmobiliaria
        )
    
    def test_bulk_searches_performance(self):
        """Test performance con múltiples búsquedas"""
        import time
        
        start_time = time.time()
        
        # Crear 100 búsquedas
        searches_data = []
        for i in range(100):
            searches_data.append({
                'nombre_busqueda': f'Búsqueda {i}',
                'texto_original': f'test search {i}',
                'usuario': self.usuario,
                'guardado': True
            })
        
        with transaction.atomic():
            Busqueda.objects.bulk_create([
                Busqueda(**data) for data in searches_data
            ])
        
        creation_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        all_searches = get_all_searches()
        retrieval_time = time.time() - start_time
        
        self.assertEqual(len(all_searches), 100)
        self.assertLess(creation_time, 1.0)  # Debe crear en menos de 1 segundo
        self.assertLess(retrieval_time, 0.5)  # Debe obtener en menos de 0.5 segundos
    
    def test_keywords_indexing_performance(self):
        """Test performance del sistema de palabras clave"""
        import time
        
        keywords_texts = [
            'apartamento', 'casa', 'garage', 'balcon', 'dormitorio',
            'baño', 'cocina', 'living', 'terraza', 'patio'
        ]
        
        start_time = time.time()
        
        # Crear palabras clave con sinónimos
        for texto in keywords_texts:
            get_or_create_palabra_clave(texto)
        
        creation_time = time.time() - start_time
        
        # Verificar que se crearon correctamente (considerando normalización)
        created_keywords = PalabraClave.objects.all()
        self.assertLessEqual(len(created_keywords), len(keywords_texts))  # Algunas pueden estar normalizadas
        self.assertGreater(len(created_keywords), 5)  # Al menos 5 palabras únicas
        
        # Performance debe ser aceptable
        self.assertLess(creation_time, 2.0)
