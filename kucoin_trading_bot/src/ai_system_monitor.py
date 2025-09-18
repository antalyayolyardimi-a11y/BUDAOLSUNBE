"""
🚀 AI Optimizer Sistem Durumu ve Kontrol Paneli
Gelişmiş AI optimizasyon sisteminin durumunu izle
"""

import json
import os
from datetime import datetime, timedelta

def check_ai_system_status():
    """AI optimizasyon sisteminin durumunu kontrol et"""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_health': 'healthy',
            'components': {},
            'recent_optimizations': [],
            'performance_summary': {},
            'recommendations': []
        }
        
        # 📊 Optimizasyon geçmişini kontrol et
        history_file = "data/optimization_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
                status['recent_optimizations'] = history[-5:]  # Son 5 optimizasyon
                status['components']['optimization_history'] = 'active'
        else:
            status['components']['optimization_history'] = 'not_found'
        
        # 🎯 Signal tracker durumu
        signal_perf_file = "data/signal_performance.json"
        if os.path.exists(signal_perf_file):
            status['components']['signal_tracker'] = 'active'
        else:
            status['components']['signal_tracker'] = 'not_found'
        
        # ⚙️ Mevcut ayarlar
        settings_file = "data/current_optimizer_settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                status['current_settings'] = settings
                status['components']['settings'] = 'active'
        else:
            status['components']['settings'] = 'default'
        
        # 🔍 Sistem sağlığı değerlendirmesi
        active_components = sum(1 for comp in status['components'].values() if comp == 'active')
        total_components = len(status['components'])
        
        if active_components == total_components:
            status['system_health'] = 'excellent'
        elif active_components >= total_components * 0.7:
            status['system_health'] = 'good'
        elif active_components >= total_components * 0.5:
            status['system_health'] = 'fair'
        else:
            status['system_health'] = 'needs_attention'
        
        # 📈 Performans özeti
        if status['recent_optimizations']:
            recent_opt = status['recent_optimizations'][-1]
            status['performance_summary'] = {
                'last_optimization': recent_opt.get('timestamp'),
                'last_optimization_type': recent_opt.get('optimization_type'),
                'total_optimizations_today': len([
                    opt for opt in status['recent_optimizations'] 
                    if opt.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))
                ])
            }
        
        return status
        
    except Exception as e:
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': 'error',
            'error': str(e),
            'components': {},
            'recent_optimizations': [],
            'performance_summary': {},
            'recommendations': ['system_check_required']
        }

def print_ai_status_report():
    """AI sistem durumu raporunu yazdır"""
    status = check_ai_system_status()
    
    print("\n" + "="*60)
    print("🚀 GELİŞMİŞ AI OPTİMİZASYON SİSTEMİ DURUMU")
    print("="*60)
    
    # Sistem sağlığı
    health_icon = {
        'excellent': '🟢',
        'good': '🟡', 
        'fair': '🟠',
        'needs_attention': '🔴',
        'error': '❌'
    }
    
    print(f"Sistem Sağlığı: {health_icon.get(status['system_health'], '❓')} {status['system_health'].upper()}")
    print(f"Son Kontrol: {status['timestamp']}")
    print()
    
    # Bileşen durumları
    print("📊 BİLEŞEN DURUMLARI:")
    for component, state in status['components'].items():
        state_icon = '🟢' if state == 'active' else '🟡' if state == 'default' else '🔴'
        print(f"  {state_icon} {component}: {state}")
    print()
    
    # Son optimizasyonlar
    if status['recent_optimizations']:
        print("🎯 SON OPTİMİZASYONLAR:")
        for opt in status['recent_optimizations'][-3:]:
            opt_time = opt.get('timestamp', 'unknown')[:16].replace('T', ' ')
            opt_type = opt.get('optimization_type', 'unknown')
            print(f"  ⚙️ {opt_time} - {opt_type}")
    else:
        print("🎯 SON OPTİMİZASYONLAR: Henüz optimizasyon yapılmamış")
    print()
    
    # Performans özeti
    if status['performance_summary']:
        print("📈 PERFORMANS ÖZETİ:")
        perf = status['performance_summary']
        if perf.get('last_optimization'):
            print(f"  🕐 Son Optimizasyon: {perf['last_optimization'][:16].replace('T', ' ')}")
        if perf.get('last_optimization_type'):
            print(f"  🔧 Son Optimizasyon Tipi: {perf['last_optimization_type']}")
        print(f"  📊 Bugünkü Optimizasyonlar: {perf.get('total_optimizations_today', 0)}")
    else:
        print("📈 PERFORMANS ÖZETİ: Veri bulunmuyor")
    print()
    
    # Öneriler
    if status.get('recommendations'):
        print("💡 ÖNERİLER:")
        for rec in status['recommendations']:
            print(f"  🔸 {rec}")
    else:
        print("💡 ÖNERİLER: Sistem optimal çalışıyor")
    
    print("="*60)
    print()

if __name__ == "__main__":
    print_ai_status_report()