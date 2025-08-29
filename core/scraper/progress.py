from datetime import datetime
import os
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def tomar_captura_debug(driver, motivo="debug"):
    try:
        debug_dir = os.path.join('static', 'debug_screenshots')
        os.makedirs(debug_dir, exist_ok=True)
        staticfiles_debug_dir = os.path.join('staticfiles', 'debug_screenshots')
        os.makedirs(staticfiles_debug_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{motivo}_{timestamp}"

        screenshot_path = os.path.join(debug_dir, f"{filename_base}.png")
        staticfiles_screenshot_path = os.path.join(staticfiles_debug_dir, f"{filename_base}.png")

        driver.save_screenshot(screenshot_path)
        try:
            import shutil
            shutil.copy2(screenshot_path, staticfiles_screenshot_path)
        except Exception:
            pass

        html_path = os.path.join(debug_dir, f"{filename_base}.html")
        staticfiles_html_path = os.path.join(staticfiles_debug_dir, f"{filename_base}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        try:
            with open(staticfiles_html_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
        except Exception:
            pass

        info_path = os.path.join(debug_dir, f"{filename_base}_info.txt")
        staticfiles_info_path = os.path.join(staticfiles_debug_dir, f"{filename_base}_info.txt")
        info_content = (
            f"Motivo: {motivo}\n"
            f"URL: {driver.current_url}\n"
            f"Título: {driver.title}\n"
            f"Timestamp: {timestamp}\n"
            f"Window Size: {driver.get_window_size()}\n"
        )
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(info_content)
        try:
            with open(staticfiles_info_path, 'w', encoding='utf-8') as f:
                f.write(info_content)
        except Exception:
            pass

        print(f"📸 [DEBUG] Captura guardada: {screenshot_path}")
        print(f"📄 [DEBUG] HTML guardado: {html_path}")
        print(f"ℹ️  [DEBUG] Info guardada: {info_path}")

        return f"/static/debug_screenshots/{filename_base}.png"
    except Exception as e:
        print(f"❌ [DEBUG] Error tomando captura: {e}")
        return None


def send_progress_update(total_found=None, estimated_time=None, current_search_item=None, matched_publications=None, final_message=None, page_items_found=None, debug_screenshot=None, all_matched_properties=None):
    if final_message:
        print(f'✅ [FINAL] {final_message}')
    elif current_search_item and not current_search_item.startswith("Búsqueda actual"):
        print(f'🔄 [PROGRESO] {current_search_item}')

    if debug_screenshot:
        try:
            import json
            debug_file = os.path.join('static', 'debug_screenshots', 'latest_screenshots.json')
            screenshots = []
            if os.path.exists(debug_file):
                try:
                    with open(debug_file, 'r', encoding='utf-8') as f:
                        screenshots = json.load(f)
                except Exception:
                    screenshots = []
            screenshots.append({
                'path': debug_screenshot,
                'timestamp': datetime.now().isoformat(),
                'message': current_search_item or 'Debug screenshot'
            })
            screenshots = screenshots[-10:]
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(screenshots, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ [DEBUG] Error guardando lista de capturas: {e}")

    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print("⚠️ [WebSocket] Channel layer no disponible - funciona sin Redis/Daphne")
            return
        async_to_sync(channel_layer.group_send)(
            "search_progress",
            {
                "type": "send_progress",
                "message": {
                    "total_found": total_found,
                    "estimated_time": estimated_time,
                    "current_search_item": current_search_item,
                    "matched_publications": matched_publications,
                    "final_message": final_message,
                    "page_items_found": page_items_found,
                    "debug_screenshot": debug_screenshot,
                    "all_matched_properties": all_matched_properties,
                }
            }
        )
    except Exception as e:
        print(f"⚠️ [WebSocket] Error: {e}")
