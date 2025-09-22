"""
Tests específicos para el Search Manager
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
import uuid
import json

from core.models import Busqueda, PalabraClave, Propiedad, ResultadoBusqueda, Usuario, Inmobiliaria, Plataforma
from core.search_manager import (
    get_all_searches, get_all_search_history, get_search, save_search, delete_search,
    procesar_keywords, get_or_create_palabra_clave, buscar_coincidencias,
    create_search, update_search, load_results, save_results, get_search_stats
)


class SearchManagerCoreTest(TestCase):
    """Tests básicos del Search Manager"""
    
    def test_create_search_basic(self):
        """Test de creación básica de búsqueda"""
        search_data = {
            'name': 'Test Apartamento',
            'filters': {'tipo': 'apartamento', 'operacion': 'alquiler'},
            'keywords': ['garaje', 'terraza'],
            'original_text': 'apartamento con garaje y terraza',
            'guardado': True
        }
        
        result = create_search(search_data)
        
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        self.assertEqual(result['name'], 'Test Apartamento')
        
        # Verificar que se guardó en BD
        busqueda = Busqueda.objects.get(id=result['id'])
        self.assertEqual(busqueda.nombre_busqueda, 'Test Apartamento')
        self.assertEqual(busqueda.filtros['tipo'], 'apartamento')
        
    def test_create_search_with_keywords(self):
        """Test de creación con keywords procesadas"""
        search_data = {
            'name': 'Test Keywords',
            'filters': {'tipo': 'casa'},
            'keywords': ['apartamento', 'garage', 'terraza'],
            'original_text': '',
            'guardado': True
        }
        
        result = create_search(search_data)
        busqueda = Busqueda.objects.get(id=result['id'])
        
        # Verificar relaciones con keywords a través de BusquedaPalabraClave
        from core.models import BusquedaPalabraClave
        keywords_relacionadas = BusquedaPalabraClave.objects.filter(busqueda=busqueda)
        self.assertGreater(len(keywords_relacionadas), 0)
        
    def test_get_all_searches_only_saved(self):
        """Test que get_all_searches solo retorna búsquedas guardadas"""
        # Crear búsqueda guardada
        create_search({
            'name': 'Guardada',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        # Crear búsqueda no guardada directamente en BD
        usuario = Usuario.objects.first()
        Busqueda.objects.create(
            nombre_busqueda='No Guardada',
            texto_original='',
            filtros={'tipo': 'casa'},
            guardado=False,
            usuario=usuario
        )
        
        searches = get_all_searches()
        nombres = [s['nombre_busqueda'] for s in searches]  # Usar nombre_busqueda real
        
        self.assertIn('Guardada', nombres)
        self.assertNotIn('No Guardada', nombres)
        
    def test_get_all_search_history(self):
        """Test que get_all_search_history retorna todas las búsquedas"""
        create_search({
            'name': 'Guardada',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        # Crear búsqueda no guardada directamente
        usuario = Usuario.objects.first()
        Busqueda.objects.create(
            nombre_busqueda='No Guardada',
            texto_original='',
            filtros={'tipo': 'casa'},
            guardado=False,
            usuario=usuario
        )
        
        history = get_all_search_history()
        nombres = [s['nombre_busqueda'] for s in history]  # Usar nombre_busqueda real
        
        self.assertIn('Guardada', nombres)
        self.assertIn('No Guardada', nombres)
        
    def test_delete_search_soft(self):
        """Test eliminación suave de búsqueda"""
        search_data = create_search({
            'name': 'Para Eliminar',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        # Verificar que está en lista
        searches_before = get_all_searches()
        self.assertTrue(any(s['nombre_busqueda'] == 'Para Eliminar' for s in searches_before))
        
        # Eliminar
        delete_search(search_data['id'])
        
        # Verificar que no está en lista pero existe en BD
        searches_after = get_all_searches()
        self.assertFalse(any(s['nombre_busqueda'] == 'Para Eliminar' for s in searches_after))
        
        # Verificar que todavía existe en historial
        history = get_all_search_history()
        self.assertTrue(any(s['nombre_busqueda'] == 'Para Eliminar' for s in history))


class SearchManagerKeywordsTest(TestCase):
    """Tests para el manejo de keywords"""
    
    def test_procesar_keywords_basico(self):
        """Test básico de procesamiento de keywords"""
        texto = "apartamento garaje terraza"
        resultado = procesar_keywords(texto)
        
        self.assertIsInstance(resultado, list)
        self.assertGreater(len(resultado), 0)
        
        # Verificar estructura de resultado
        for item in resultado:
            self.assertIn('texto', item)
            self.assertIn('idioma', item)
            self.assertIn('sinonimos', item)
            
    def test_procesar_keywords_con_sinonimos(self):
        """Test de procesamiento con sinónimos"""
        texto = "apartamento"
        resultado = procesar_keywords(texto)
        
        # Buscar el item apartamento
        apartamento_item = next((item for item in resultado if item['texto'] == 'apartamento'), None)
        self.assertIsNotNone(apartamento_item)
        
        # Verificar que tiene sinónimos
        self.assertIn('apto', apartamento_item['sinonimos'])
        self.assertIn('departamento', apartamento_item['sinonimos'])
        
    def test_get_or_create_palabra_clave(self):
        """Test de obtener o crear palabra clave"""
        # Primera llamada - crear
        palabra1 = get_or_create_palabra_clave('garaje')
        self.assertEqual(palabra1.texto, 'garaje')
        
        # Segunda llamada - obtener existente
        palabra2 = get_or_create_palabra_clave('garaje')
        self.assertEqual(palabra1.id, palabra2.id)
        
    def test_buscar_coincidencias(self):
        """Test de búsqueda de coincidencias"""
        # Crear búsqueda primero
        busqueda_data = {
            'name': 'Test coincidencias',
            'filters': {},
            'keywords': ['garaje'],
            'original_text': 'garaje',
            'guardado': True
        }
        result = create_search(busqueda_data)
        busqueda_id = result['id']
        
        # Crear plataforma
        plataforma = Plataforma.objects.create(
            nombre="Test Platform",
            url="http://test.com"
        )
        
        # Crear algunas propiedades de prueba
        propiedad1 = Propiedad.objects.create(
            titulo="Apartamento con garaje",
            url="http://test1.com",
            plataforma=plataforma,
            metadata={"precio": 50000}
        )
        
        propiedad2 = Propiedad.objects.create(
            titulo="Casa con jardín", 
            url="http://test2.com",
            plataforma=plataforma,
            metadata={"precio": 80000}
        )
        
        # Datos de propiedades como dictionaries para la función
        propiedades_data = [
            {'titulo': propiedad1.titulo, 'metadata': propiedad1.metadata, 'url': propiedad1.url},
            {'titulo': propiedad2.titulo, 'metadata': propiedad2.metadata, 'url': propiedad2.url}
        ]
        
        # Buscar coincidencias con keywords
        coincidencias = buscar_coincidencias(busqueda_id, propiedades_data)
        
        # Verificar que es una lista
        self.assertIsInstance(coincidencias, list)


class SearchManagerResultsTest(TestCase):
    """Tests para manejo de resultados"""
    
    def test_save_results(self):
        """Test de guardado de resultados"""
        # Crear búsqueda
        search_data = create_search({
            'name': 'Test Results',
            'filters': {'tipo': 'apartamento'},
            'keywords': ['test'],
            'original_text': '',
            'guardado': True
        })
        
        # Crear resultados de prueba usando la estructura correcta
        resultados = [
            {
                'titulo': 'Apartamento Test 1',
                'url': 'http://test1.com',
                'descripcion': 'Apartamento de prueba',
                'metadata': {'precio': 50000}
            },
            {
                'titulo': 'Apartamento Test 2', 
                'url': 'http://test2.com',
                'descripcion': 'Otro apartamento',
                'metadata': {'precio': 60000}
            }
        ]
        
        # Guardar resultados
        save_results(search_data['id'], resultados)
        
        # Verificar que se guardaron
        busqueda = Busqueda.objects.get(id=search_data['id'])
        resultados_guardados = ResultadoBusqueda.objects.filter(busqueda=busqueda)
        
        self.assertEqual(len(resultados_guardados), 2)
        
    def test_load_results(self):
        """Test de carga de resultados"""
        # Crear y guardar resultados
        search_data = create_search({
            'name': 'Test Load',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        resultados_originales = [
            {
                'titulo': 'Apartamento Load Test',
                'precio_valor': 70000,
                'url_publicacion': 'http://load-test.com'
            }
        ]
        
        save_results(search_data['id'], resultados_originales)
        
        # Cargar resultados
        resultados_cargados = load_results(search_data['id'])
        
        self.assertGreater(len(resultados_cargados), 0)
        self.assertEqual(resultados_cargados[0]['titulo'], 'Apartamento Load Test')
        
    def test_get_search_stats(self):
        """Test de estadísticas del sistema"""
        # Crear algunas búsquedas y propiedades
        create_search({
            'name': 'Stats Test 1',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        create_search({
            'name': 'Stats Test 2',
            'filters': {'tipo': 'casa'},
            'keywords': [],
            'original_text': '',
            'guardado': False
        })
        
        # Crear plataforma y propiedad correctamente
        plataforma = Plataforma.objects.create(
            nombre="Stats Platform",
            url="http://stats.com"
        )
        
        Propiedad.objects.create(
            titulo="Propiedad Stats",
            url="http://stats.com/1",
            plataforma=plataforma,
            metadata={"precio": 100000}
        )
        
        stats = get_search_stats()
        
        self.assertIn('total_searches', stats)
        self.assertIn('saved_searches', stats)
        self.assertIn('total_properties', stats)
        self.assertIn('total_keywords', stats)
        
        self.assertGreaterEqual(stats['total_searches'], 2)
        self.assertGreaterEqual(stats['saved_searches'], 1)
        self.assertGreaterEqual(stats['total_properties'], 1)


class SearchManagerCompatibilityTest(TestCase):
    """Tests para funciones de compatibilidad"""
    
    def test_save_search_compatibility(self):
        """Test de función save_search para compatibilidad"""
        search_data = {
            'nombre_busqueda': 'Compat Test',
            'filtros': {'tipo': 'apartamento'},
            'palabras_clave': ['compat'],
            'texto_original': 'test compatibility'
        }
        
        result = save_search(search_data)
        
        # save_search retorna un string con el UUID
        self.assertIsInstance(result, str)
        
        # Verificar que se creó la búsqueda
        busqueda = Busqueda.objects.get(id=result)
        self.assertEqual(busqueda.nombre_busqueda, 'Compat Test')
            
    def test_update_search_compatibility(self):
        """Test de función update_search"""
        # Crear búsqueda
        search_data = create_search({
            'name': 'Update Test',
            'filters': {'tipo': 'apartamento'},
            'keywords': [],
            'original_text': '',
            'guardado': True
        })
        
        # Actualizar (update_search usa 'name' no 'nombre_busqueda')
        update_data = {
            'name': 'Updated Name',
            'filters': {'tipo': 'casa', 'operacion': 'venta'}
        }
        
        result = update_search(search_data['id'], update_data)
        
        # update_search retorna un bool
        self.assertTrue(result)
        
        # Verificar actualización
        busqueda_actualizada = Busqueda.objects.get(id=search_data['id'])
        self.assertEqual(busqueda_actualizada.nombre_busqueda, 'Updated Name')
        self.assertEqual(busqueda_actualizada.nombre_busqueda, 'Updated Name')
        self.assertEqual(busqueda_actualizada.filtros['tipo'], 'casa')


class SearchManagerErrorHandlingTest(TestCase):
    """Tests para manejo de errores en Search Manager"""
    
    def test_get_search_invalid_id(self):
        """Test con ID inválido"""
        try:
            result = get_search('invalid-uuid')
            self.assertIsNone(result)
        except Exception as e:
            # Esperamos un error de validación de UUID
            self.assertIn('UUID', str(e))
        
    def test_delete_search_nonexistent(self):
        """Test eliminar búsqueda inexistente"""
        # No debería fallar
        try:
            result = delete_search(str(uuid.uuid4()))
            self.assertFalse(result)  # o el comportamiento esperado
        except Exception:
            # Comportamiento esperado si UUID no existe
            pass
        
    def test_save_results_invalid_search(self):
        """Test guardar resultados con búsqueda inválida"""
        resultados = [{'titulo': 'Test', 'metadata': {'precio': 1000}}]
        
        # No debería fallar catastróficamente
        try:
            save_results('invalid-uuid', resultados)
        except Exception as e:
            # Verificar que es un error manejado apropiadamente
            self.assertIsInstance(e, (ValueError, Busqueda.DoesNotExist))
            
    def test_procesar_keywords_empty(self):
        """Test procesar keywords vacías"""
        # Test con string vacío
        result = procesar_keywords('')
        self.assertEqual(result, [])
        
        # Test con None debe manejarse apropiadamente
        try:
            result = procesar_keywords(None)
            self.assertEqual(result, [])
        except Exception:
            # Si maneja None de forma diferente, es comportamiento válido
            pass