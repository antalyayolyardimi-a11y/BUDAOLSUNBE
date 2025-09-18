"""
AI Optimizer Performance Extension
Performans takip ve gelişmiş analiz fonksiyonları
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter

def get_performance_metrics(self, failed_signals):
    """Başarısız sinyallerden performans metrikleri hesapla"""
    try:
        if not failed_signals:
            return {
                'success_rate': 100.0,
                'avg_failure_score': 0.0,
                'dominant_failure_types': [],
                'symbol_performance': {},
                'timeframe_performance': {},
                'optimization_priority': 'maintain'
            }
        
        # 📊 Temel metrikler
        total_signals = len(failed_signals)
        failure_types = [signal.get('failure_reason', 'unknown') for signal in failed_signals]
        failure_scores = [signal.get('confidence_score', 0) for signal in failed_signals]
        
        # 🎯 Dominant hata tipleri
        from collections import Counter
        failure_counter = Counter(failure_types)
        dominant_failures = failure_counter.most_common(3)
        
        # 📈 Sembol bazında performans
        symbol_performance = {}
        for signal in failed_signals:
            symbol = signal.get('symbol', 'unknown')
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'count': 0, 'avg_score': 0}
            symbol_performance[symbol]['count'] += 1
            symbol_performance[symbol]['avg_score'] += signal.get('confidence_score', 0)
        
        # Ortalama skorları hesapla
        for symbol in symbol_performance:
            if symbol_performance[symbol]['count'] > 0:
                symbol_performance[symbol]['avg_score'] /= symbol_performance[symbol]['count']
        
        # ⏰ Zaman bazında performans
        timeframe_performance = {}
        for signal in failed_signals:
            timestamp = signal.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = timestamp.hour
            
            if hour not in timeframe_performance:
                timeframe_performance[hour] = 0
            timeframe_performance[hour] += 1
        
        return {
            'success_rate': max(0, 100 - (total_signals * 10)),  # Her başarısız sinyal %10 düşürür
            'avg_failure_score': sum(failure_scores) / len(failure_scores) if failure_scores else 0,
            'dominant_failure_types': [f[0] for f in dominant_failures],
            'symbol_performance': symbol_performance,
            'timeframe_performance': timeframe_performance,
            'optimization_priority': self._determine_optimization_priority(failure_counter)
        }
        
    except Exception as e:
        self.logger.error(f"Performans metrikleri hesaplama hatası: {e}")
        return {
            'success_rate': 50.0,
            'avg_failure_score': 50.0,
            'dominant_failure_types': ['calculation_error'],
            'symbol_performance': {},
            'timeframe_performance': {},
            'optimization_priority': 'high'
        }

def _determine_optimization_priority(self, failure_counter):
    """Hata sayısına göre optimizasyon önceliği belirle"""
    total_failures = sum(failure_counter.values())
    
    if total_failures >= 20:
        return 'critical'
    elif total_failures >= 10:
        return 'high'
    elif total_failures >= 5:
        return 'medium'
    else:
        return 'low'

def save_optimization_result(self, optimization_type, old_params, new_params, performance_improvement):
    """Optimizasyon sonucunu kaydet"""
    try:
        result = {
            'timestamp': datetime.now().isoformat(),
            'optimization_type': optimization_type,
            'old_parameters': old_params,
            'new_parameters': new_params,
            'performance_improvement': performance_improvement,
            'applied': True
        }
        
        self.optimization_history_data.append(result)
        
        # Dosyaya kaydet
        os.makedirs('data', exist_ok=True)
        with open(self.optimization_history, 'w') as f:
            json.dump(self.optimization_history_data, f, indent=2)
            
        self.logger.info(f"✅ {optimization_type} optimizasyonu kaydedildi")
        
    except Exception as e:
        self.logger.error(f"Optimizasyon sonucu kaydetme hatası: {e}")

def get_optimization_recommendations(self, performance_metrics):
    """Performans metriklerine göre optimizasyon önerileri"""
    recommendations = []
    
    priority = performance_metrics.get('optimization_priority', 'low')
    dominant_failures = performance_metrics.get('dominant_failure_types', [])
    success_rate = performance_metrics.get('success_rate', 100)
    
    if success_rate < 50:
        recommendations.append({
            'type': 'critical',
            'action': 'comprehensive_optimization',
            'reason': f'Başarı oranı çok düşük: %{success_rate:.1f}'
        })
    
    if 'low_confidence' in dominant_failures:
        recommendations.append({
            'type': 'entry_precision',
            'action': 'increase_precision_threshold',
            'reason': 'Düşük güven skorlu sinyaller dominant'
        })
    
    if 'market_volatility' in dominant_failures:
        recommendations.append({
            'type': 'risk_management',
            'action': 'adjust_stop_loss',
            'reason': 'Piyasa volatilitesi yüksek'
        })
    
    if 'volume_insufficient' in dominant_failures:
        recommendations.append({
            'type': 'volume_analysis',
            'action': 'increase_volume_threshold',
            'reason': 'Yetersiz volume sinyalleri'
        })
    
    return recommendations