import json
import uuid
from channels.generic.websocket import WebsocketConsumer

class SearchProgressConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_id = None
        self.room_group_name = 'search_progress'

    def connect(self):
        print('[DEPURACIÓN] WebSocket conectado')
        # Unirse al grupo para recibir actualizaciones del scraper
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

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
                print(f'🤖 [DEPURACIÓN] Resultado IA: {ia_result}')
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

                # Extraer parámetros de los filtros para run_scraper con mapeo mejorado
                tipo_raw = filtros.get('tipo_inmueble') or filtros.get('tipo')
                print(f'🔍 [DEBUG] tipo_raw extraído: {tipo_raw}')
                
                # Normalizar tipo de inmueble para MercadoLibre (singular → plural minúscula)
                if tipo_raw:
                    tipo_map = {
                        'apartamento': 'apartamentos',
                        'casa': 'casas', 
                        'terreno': 'terrenos',
                        'oficina': 'oficinas',
                        'local': 'locales'
                    }
                    tipo_inmueble = tipo_map.get(tipo_raw.lower(), tipo_raw.lower())
                    print(f'🔍 [DEBUG] tipo_raw.lower(): {tipo_raw.lower()}, mapeado a: {tipo_inmueble}')
                else:
                    tipo_inmueble = None
                    print(f'🔍 [DEBUG] tipo_raw es None o vacío, tipo_inmueble = None')
                
                operacion = filtros.get('operacion', 'venta')
                
                # Usar ciudad si está disponible, sino departamento
                ubicacion = filtros.get('ciudad') or filtros.get('departamento', 'montevideo')
                
                # Mapear precios desde diferentes campos posibles
                precio_min = filtros.get('precio_min') or filtros.get('precio_desde')
                precio_max = filtros.get('precio_max') or filtros.get('precio_hasta')
                
                print(f'🚀 [DEPURACIÓN] Mapeo de filtros:')
                print(f'   - tipo_raw: {tipo_raw} → tipo_inmueble: {tipo_inmueble}')
                print(f'   - ciudad: {filtros.get("ciudad")}, departamento: {filtros.get("departamento")} → ubicacion: {ubicacion}')
                print(f'   - precio_min: {precio_min}, precio_max: {precio_max}')
                print(f'🚀 [DEPURACIÓN] Llamando run_scraper con: tipo={tipo_inmueble}, operacion={operacion}, ubicacion={ubicacion}, precio_min={precio_min}, precio_max={precio_max}')
                print(f'⚠️  [MODO SECUENCIAL] Usando 1 worker por fase para evitar problemas de concurrencia')
                
                # Llamar al scraper (esto ejecutará todo el proceso con logs)
                # TEMPORAL: Usando 1 worker para evitar problemas de concurrencia
                run_scraper(
                    tipo_inmueble=tipo_inmueble,
                    operacion=operacion, 
                    ubicacion=ubicacion,
                    max_paginas=2,  # Limitamos para pruebas
                    precio_min=precio_min,
                    precio_max=precio_max,
                    workers_fase1=1,  # DESHABILITAR CONCURRENCIA: era 3, ahora 1
                    workers_fase2=1   # DESHABILITAR CONCURRENCIA: era 3, ahora 1
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
        print(f'📡 [WEBSOCKET] Enviando a cliente: {message.get("current_search_item", "Sin mensaje")[:100]}{"..." if len(str(message.get("current_search_item", ""))) > 100 else ""}')
        if message.get("total_found"):
            print(f'📊 [WEBSOCKET] Total encontrado: {message["total_found"]:,}')
        self.send(text_data=json.dumps({
            'message': message
        }))
