import json
import uuid
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
                self.send(text_data=json.dumps({'message': 'Texto procesado por IA', 'ia_result': ia_result}))
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
                self.send(text_data=json.dumps({'message': 'Filtros fusionados', 'filters': filtros_final}))
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
            except Exception as e:
                print(f'🛑 [DEPURACIÓN] Error construyendo JSON final: {e}')
                self.send(text_data=json.dumps({'message': 'Error construyendo JSON final', 'error': str(e)}))
                return

            # Verificar parada antes del scraper
            if is_search_stopped(self.search_id):
                self.send(text_data=json.dumps({'message': 'Búsqueda detenida por el usuario'}))
                return

            # Mensaje: inicio scraper
            print('🔍 [DEPURACIÓN] Antes de ejecutar scraper')
            self.send(text_data=json.dumps({'message': 'Ejecutando scraper...'}))
            try:
                from core.scraper import run_scraper
                filtros = resultado_busqueda['filters']
                keywords = resultado_busqueda['keywords']
                if isinstance(keywords, str):
                    keywords = [keywords] if keywords else []
                print(f'🔍 [DEPURACIÓN] Ejecutando scraper con filtros: {filtros} y keywords: {keywords}')
                
                print(f'🚀 [DEPURACIÓN] Llamando run_scraper con TODOS los filtros')
                print(f'⚠️  [MODO SECUENCIAL] Usando 1 worker por fase para evitar problemas de concurrencia')
                
                # Llamar al scraper con todos los filtros (nueva signatura)
                # TEMPORAL: Usando 1 worker para evitar problemas de concurrencia
                run_scraper(
                    filters=filtros,           # Pasar TODOS los filtros
                    keywords=keywords,         # Pasar las keywords
                    max_paginas=2,            # Limitamos para pruebas
                    workers_fase1=1,          # DESHABILITAR CONCURRENCIA: era 3, ahora 1
                    workers_fase2=1           # DESHABILITAR CONCURRENCIA: era 3, ahora 1
                )
                
                print(f'✅ [DEPURACIÓN] run_scraper completado exitosamente')
                
                # Verificar una última vez si se detuvo
                if is_search_stopped(self.search_id):
                    self.send(text_data=json.dumps({'message': {'final_message': 'Búsqueda detenida por el usuario'}}))
                    return
                
                # run_scraper ya envía el mensaje de finalización por WebSocket
                # No necesitamos hacer nada más aquí
                
            except Exception as e:
                print(f'🛑 [DEPURACIÓN] Error en el scraper: {e}')
                self.send(text_data=json.dumps({
                    'message': {'final_message': f'Error en el scraper: {str(e)}'}
                }))
            finally:
                # Desregistrar búsqueda al finalizar
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
