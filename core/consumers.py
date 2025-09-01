import json
import uuid
from datetime import datetime
from channels.generic.websocket import WebsocketConsumer

class SearchProgressConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_id = None
        self.room_group_name = 'search_progress'

    def connect(self):
        print('[🔌 WEBSOCKET] Cliente conectando...')
        try:
            # Unirse al grupo para recibir actualizaciones del scraper
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            
            # Verificar que channel_layer esté disponible
            if channel_layer is None:
                print('[❌ WEBSOCKET] Channel layer no disponible')
                self.close()
                return
            
            async_to_sync(channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.accept()
            print('[✅ WEBSOCKET] Cliente conectado exitosamente')
            
        except Exception as e:
            print(f'[❌ WEBSOCKET] Error al conectar: {e}')
            self.close()

    def disconnect(self, close_code):
        print(f'[DEPURACIÓN] WebSocket desconectado. Código: {close_code}')
        # Salir del grupo
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        # Desregistrar búsqueda activa al desconectar
        if self.search_id:
            from core.views import unregister_active_search
            unregister_active_search(self.search_id)

    def receive(self, text_data):
        print(f'🔥 [CONSUMER] Mensaje recibido por WebSocket: {text_data}')
        try:
            data = json.loads(text_data)
            print(f'🔥 [CONSUMER] JSON parseado correctamente: {data}')

            # Extraer información de guardado desde el principio
            should_save = data.get('guardar', False)
            search_name = data.get('name', '')
            print(f'💾 [CONSUMER] Guardar búsqueda: {should_save}, Nombre: "{search_name}"')

            # Generar ID único para esta búsqueda y registrarla como activa
            self.search_id = str(uuid.uuid4())
            from core.views import register_active_search, is_search_stopped
            register_active_search(self.search_id)
            print(f'🔥 [CONSUMER] Búsqueda registrada con ID: {self.search_id}')

            # Verificar si debe detenerse antes de cada paso
            if is_search_stopped(self.search_id):
                self.send(text_data=json.dumps({'message': 'Búsqueda detenida por el usuario'}))
                return

            # Mensaje: inicio procesamiento IA
            print('🤖 [DEPURACIÓN] Antes de procesar texto con IA')
            self.send(text_data=json.dumps({'message': 'Procesando texto con IA...'}))
            try:
                from asgiref.sync import async_to_sync
                from core.views import analyze_query_with_ia
                query_text = data.get('texto', '')
                print(f'🤖 [DEPURACIÓN] Procesando texto con IA: "{query_text}"')
                
                # Verificar parada antes de llamar IA
                if is_search_stopped(self.search_id):
                    self.send(text_data=json.dumps({'message': 'Búsqueda detenida por el usuario'}))
                    return
                
                ia_result = async_to_sync(analyze_query_with_ia)(query_text)
                print(f'\n🤖 [DEPURACIÓN] Resultado IA: {ia_result}\n')
                
                # Enviar resultado de IA al frontend para debugging
                self.send(text_data=json.dumps({
                    'message': 'Texto procesado por IA', 
                    'ia_result': ia_result,
                    'debug_ia': {
                        'texto_original': query_text,
                        'filtros_extraidos': ia_result.get('filters', {}),
                        'keywords_extraidas': ia_result.get('keywords', [])
                    }
                }))
            except Exception as e:
                print(f'🤖 [DEPURACIÓN] Error procesando texto con IA: {e}')
                self.send(text_data=json.dumps({'message': 'Error procesando texto con IA', 'error': str(e)}))
                return

            # Verificar parada antes de fusionar filtros
            if is_search_stopped(self.search_id):
                self.send(text_data=json.dumps({'message': 'Búsqueda detenida por el usuario'}))
                return

            # Mensaje: fusión de filtros
            print('🎚️ [DEPURACIÓN] Antes de fusionar filtros')
            self.send(text_data=json.dumps({'message': 'Fusionando filtros manuales y textuales...'}))
            try:
                filtros_manual = data.get('filtros', {})
                filtros_ia = ia_result.get('filters', {})
                filtros_final = filtros_manual.copy()
                for k, v in filtros_ia.items():
                    filtros_final[k] = v  # Prioriza IA si hay coincidencia
                print(f'🎚️ [DEPURACIÓN] Filtros fusionados: {filtros_final}')
                # Enviar filtros fusionados al frontend para debugging
                self.send(text_data=json.dumps({
                    'message': 'Filtros fusionados', 
                    'filters': filtros_final,
                    'debug_filtros': {
                        'filtros_manuales': filtros_manual,
                        'filtros_ia': filtros_ia,
                        'filtros_finales': filtros_final
                    }
                }))
            except Exception as e:
                print(f'🛑 [DEPURACIÓN] Error fusionando filtros: {e}')
                self.send(text_data=json.dumps({'message': 'Error fusionando filtros', 'error': str(e)}))
                return

            # Verificar parada antes de construir JSON
            if is_search_stopped(self.search_id):
                self.send(text_data=json.dumps({'message': 'Búsqueda detenida por el usuario'}))
                return

            # Construir JSON final
            print('🔨 [DEPURACIÓN] Antes de construir JSON final')
            try:
                resultado_busqueda = {
                    'filters': filtros_final,
                    'keywords': ia_result.get('keywords', ''),
                    'original_text': ia_result.get('original_text', query_text),
                    'datetime': ia_result.get('datetime', ''),
                    'irrelevant_text': ia_result.get('remaining_text', ''),
                }
                print(f'🔨 [DEPURACIÓN] JSON final para búsqueda: {resultado_busqueda}')
                self.send(text_data=json.dumps({'message': 'Búsqueda iniciada', 'data': resultado_busqueda}))

                # Guardar búsqueda si fue solicitado
                saved_search_id = None
                saved_search_name = None
                if should_save:
                    print(f'💾 [GUARDADO] Iniciando guardado de búsqueda: "{search_name}"')
                    self.send(text_data=json.dumps({'message': 'Guardando búsqueda...'}))
                    try:
                        from core.search_manager import create_search
                        search_data = {
                            'name': search_name or f'Búsqueda {datetime.now().strftime("%d/%m/%Y %H:%M")}',
                            'keywords': ia_result.get('keywords', []),
                            'original_text': query_text,
                            'filters': filtros_final
                        }
                        created_search = create_search(search_data)
                        saved_search_id = created_search.get('id')
                        saved_search_name = created_search.get('name') or search_data['name']
                        print(f'✅ [GUARDADO] Búsqueda guardada con ID: {saved_search_id} (nombre: "{saved_search_name}")')
                        # No enviar al cliente la búsqueda todavía: esperaremos hasta que termine el scraper
                        # para poder mostrar resultados y el título definitivo. Solo avisamos que quedó programada.
                        self.send(text_data=json.dumps({'message': f'Búsqueda guardada (id: {saved_search_id}), se agregará cuando finalice el proceso.'}))
                    except Exception as save_error:
                        print(f'❌ [GUARDADO] Error guardando búsqueda: {save_error}')
                        self.send(text_data=json.dumps({'message': f'Error guardando búsqueda: {str(save_error)}'}))
                        # No retornar, continuar con el scraping
            except Exception as e:
                print(f'🛑 [DEPURACIÓN] Error construyendo JSON final: {e}')
                self.send(text_data=json.dumps({'message': 'Error construyendo JSON final', 'error': str(e)}))
                return

            # Verificar parada antes del scraper
            if is_search_stopped(self.search_id):
                self.send(text_data=json.dumps({'message': 'Búsqueda detenida por el usuario'}))
                return

            # Mensaje: inicio scraper (no bloquear el hilo del WebSocket)
            print('🔍 [DEPURACIÓN] Antes de ejecutar scraper')
            self.send(text_data=json.dumps({'message': 'Ejecutando scraper...'}))
            try:
                from core.scraper import run_scraper
                filtros = resultado_busqueda['filters']
                keywords = resultado_busqueda['keywords']
                if isinstance(keywords, str):
                    keywords = [keywords] if keywords else []
                print(f'🔍 [DEPURACIÓN] Ejecutando scraper con filtros: {filtros} y keywords: {keywords}')

                print('🚀 [DEPURACIÓN] Lanzando run_scraper en un hilo en segundo plano')
                print('⚠️  [MODO SECUENCIAL] Usando 1 worker por fase para evitar problemas de concurrencia')

                # Ejecutar en un hilo para que el consumer quede libre y procese eventos WebSocket en tiempo real
                import threading
                current_search_id = self.search_id

                def _background_task():
                    try:
                        run_scraper(
                            filters=filtros,
                            keywords=keywords,
                            max_paginas=2,
                            workers_fase1=1,
                            workers_fase2=1
                        )
                        print('✅ [DEPURACIÓN] run_scraper completado (hilo)')
                        
                        # Actualizar búsqueda guardada con resultados si existe
                        if saved_search_id:
                            print(f'🔄 [ACTUALIZANDO] Actualizando búsqueda {saved_search_id} con resultados...')
                            try:
                                from core.models import Propiedad
                                from core.search_manager import update_search
                                
                                # Obtener las propiedades que coinciden con los filtros y keywords
                                propiedades = Propiedad.objects.order_by('-id')[:50]  # Últimas 50 para buscar coincidencias
                                resultados = []
                                
                                # Aplicar lógica de filtrado de keywords
                                if keywords:
                                    import unicodedata
                                    def normalizar(texto):
                                        return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII').lower()
                                    
                                    from core.scraper import extraer_variantes_keywords
                                    keywords_variantes = extraer_variantes_keywords(keywords)
                                    for prop in propiedades:
                                        meta = prop.metadata or {}
                                        caracteristicas_txt = meta.get('caracteristicas', '') or meta.get('caracteristicas_texto', '') or ''
                                        texto_propiedad = f"{prop.titulo or ''} {prop.descripcion or ''} {caracteristicas_txt}".lower()
                                        texto_norm = normalizar(texto_propiedad)
                                        keywords_norm = [normalizar(kw) for kw in keywords_variantes]
                                        
                                        # Usar lógica flexible como en el scraper
                                        from core.scraper import stemming_basico
                                        texto_stemmed = stemming_basico(texto_norm)
                                        keywords_stemmed = [stemming_basico(kw) for kw in keywords_norm]
                                        
                                        coincidencias = 0
                                        for kw_stemmed in keywords_stemmed:
                                            if kw_stemmed in texto_stemmed or any(kw_stemmed in word for word in texto_stemmed.split()):
                                                coincidencias += 1
                                        
                                        # Si coincide al menos el 70% de las keywords
                                        if len(keywords_stemmed) > 0 and coincidencias / len(keywords_stemmed) >= 0.7:
                                            resultados.append({
                                                'titulo': prop.titulo or 'Sin título',
                                                'url': prop.url or '#',
                                                'precio': (f"{meta.get('precio_valor')} {meta.get('precio_moneda','')}".strip() if meta.get('precio_valor') else 'Precio no disponible')
                                            })
                                
                                # Actualizar la búsqueda con los resultados
                                update_data = {
                                    'results': resultados,
                                    'ultima_revision': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                if update_search(saved_search_id, update_data):
                                    print(f'✅ [ACTUALIZANDO] Búsqueda actualizada con {len(resultados)} resultados')
                                    # Notificar al cliente que la búsqueda guardada fue actualizada y enviar resultados
                                    try:
                                        resultados_formatted = [
                                            {
                                                'titulo': r.get('titulo'),
                                                'url': r.get('url'),
                                                'precio': r.get('precio')
                                            } for r in resultados
                                        ]
                                    except Exception:
                                        resultados_formatted = resultados
                                    try:
                                        # Incluir el nombre de la búsqueda para que el cliente pueda mostrar el título correcto
                                        name_to_send = saved_search_name
                                        if not name_to_send:
                                            # Intentar leer desde la base si no tenemos el nombre en la closure
                                            from core.models import Busqueda
                                            try:
                                                b = Busqueda.objects.get(id=saved_search_id)
                                                name_to_send = b.nombre_busqueda
                                            except Exception:
                                                name_to_send = None

                                        update_payload = {
                                            'id': saved_search_id,
                                            'name': name_to_send,
                                            'results': resultados_formatted,
                                            'ultima_revision': update_data.get('ultima_revision')
                                        }
                                    except Exception:
                                        update_payload = {'id': saved_search_id}
                                    self.send(text_data=json.dumps({'message': {'saved_search_updated': update_payload}}))
                                else:
                                    print(f'❌ [ACTUALIZANDO] No se pudo actualizar la búsqueda {saved_search_id}')
                                    
                            except Exception as update_error:
                                print(f'❌ [ACTUALIZANDO] Error actualizando búsqueda: {update_error}')
                                
                    except Exception as e:
                        print(f'🛑 [DEPURACIÓN] Error en run_scraper (hilo): {e}')
                        # Si falla, notificar al cliente
                        self.send(text_data=json.dumps({
                            'message': {'final_message': f'Error en el scraper: {str(e)}'}
                        }))
                    finally:
                        # Desregistrar búsqueda al finalizar
                        from core.views import unregister_active_search
                        unregister_active_search(current_search_id)

                t = threading.Thread(target=_background_task, daemon=True)
                t.start()

                # No bloquear: salir del receive para que el consumer atienda los eventos group_send
                return

            except Exception as e:
                print(f'🛑 [DEPURACIÓN] Error preparando el hilo del scraper: {e}')
                self.send(text_data=json.dumps({
                    'message': {'final_message': f'Error en el scraper: {str(e)}'}
                }))
                from core.views import unregister_active_search
                unregister_active_search(self.search_id)

        except Exception as e:
            print(f'🛑 [DEPURACIÓN] [RECEIVE] Error al procesar búsqueda: {e}')
            if self.search_id:
                from core.views import unregister_active_search
                unregister_active_search(self.search_id)

    def send_progress(self, event):
        message = event['message']
        msg = message.get("current_search_item", "Sin mensaje")
        if msg is None:
            msg = "Sin mensaje"
        print(f'📡 [WEBSOCKET] Enviando a cliente: {msg[:100]}{"..." if len(str(msg)) > 100 else ""}')
        if message.get("total_found"):
            print(f'📊 [WEBSOCKET] Total encontrado: {message["total_found"]:,}')
        self.send(text_data=json.dumps({
            'message': message
        }))
