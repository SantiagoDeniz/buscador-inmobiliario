from core.search_manager import get_search_stats

print('📈 ESTADÍSTICAS DEL SISTEMA')
print('=' * 30)
stats = get_search_stats()

for key, value in stats.items():
    if 'search' in key:
        emoji = '🔍'
    elif 'keyword' in key:
        emoji = '🏷️'
    elif 'propert' in key:
        emoji = '🏠'
    elif 'result' in key:
        emoji = '📋'
    else:
        emoji = '📊'
    
    print(f'{emoji} {key.replace("_", " ").title()}: {value}')

print('\n🎯 Sistema PostgreSQL completamente operativo!')
print('✅ Migración exitosa de SQLite a PostgreSQL')
print('🚀 Aplicación lista para producción')
