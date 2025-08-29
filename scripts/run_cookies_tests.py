import os
import sys
from pathlib import Path


def main():
    # Ensure repository root is on sys.path so 'buscador' package is importable
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    print(f"[runner] repo_root added to sys.path: {repo_root}")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buscador.settings')
    try:
        import django
        django.setup()
    except Exception as e:
        print(f"[runner] Django setup failed: {e}")
        return 1

    from importlib import import_module

    print("\n🧪 Ejecutando tests de cookies (simple + sistema)\n" + "="*60)

    # Test simple (no Selenium)
    simple = import_module('test_cookies_simple')
    print("- Test imports y análisis de archivo de cookies...")
    imports_ok = simple.test_imports()
    cookies_ok = simple.test_cookies_info()
    print(f"  Resultado simple: imports={'OK' if imports_ok else 'FALLO'}, archivo={'OK' if cookies_ok else 'FALLO'}")

    # Test sistema (Selenium)
    system = import_module('test_cookies_system')
    print("\n- Test Selenium: carga desde archivo local...")
    local_ok = system.test_cookies_local()
    print("\n- Test Selenium: carga desde variable de entorno...")
    env_ok = system.test_cookies_env()

    print("\n" + "="*60)
    print("📊 RESUMEN FINAL")
    print(f"Simple imports: {'✅' if imports_ok else '❌'}  Simple archivo: {'✅' if cookies_ok else '❌'}")
    print(f"Selenium local: {'✅' if local_ok else '❌'}  Selenium env: {'✅' if env_ok else '❌'}")

    return 0 if (imports_ok and cookies_ok and local_ok and env_ok) else 2


if __name__ == '__main__':
    sys.exit(main())
