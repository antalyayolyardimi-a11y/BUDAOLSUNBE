"""
AI-Powered Trading Signal Optimizer
Başarısız sinyalleri analiz ederek bot parametrelerini optimize eder
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

class AIOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_file = "data/signal_performance.json"
        self.optimization_history = "data/optimization_history.json"
        self.current_settings = "data/current_optimizer_settings.json"
        
        # 🚀 Performans metriklerini takip et
        self.optimization_history_data = []
        self.performance_baseline = None
        self.last_optimization_time = None
        
        # 📊 Parameter ranges for advanced optimization
        self.param_ranges = {
            'ENTRY_PRECISION': {'min': 0.4, 'max': 0.9, 'step': 0.05},
            'TP_RATIO': {'min': 1.5, 'max': 4.0, 'step': 0.25},
            'SL_RATIO': {'min': 0.8, 'max': 2.5, 'step': 0.1},
            'ADX_THRESHOLD': {'min': 20.0, 'max': 35.0, 'step': 2.5},
            'OB_SCORE_MIN': {'min': 6, 'max': 10, 'step': 1},
            'VOLUME_THRESHOLD': {'min': 1.2, 'max': 2.5, 'step': 0.1},
            'LIQUIDITY_SWEEP_MIN': {'min': 5, 'max': 9, 'step': 1}
        }
        
        # Başlangıç parametreleri
        self.min_confidence_threshold = 70.0
        self.max_signals_per_hour = 12
        self.risk_reward_min = 1.5
        self.adx_threshold = 25.0
        self.volume_multiplier = 1.0
        
        self.load_current_settings()
        
    def load_current_settings(self):
        """Mevcut optimizer ayarlarını yükle"""
        try:
            if os.path.exists(self.current_settings):
                with open(self.current_settings, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.min_confidence_threshold = settings.get('min_confidence_threshold', 70.0)
                    self.max_signals_per_hour = settings.get('max_signals_per_hour', 12)
                    self.risk_reward_min = settings.get('risk_reward_min', 1.5)
                    self.adx_threshold = settings.get('adx_threshold', 25.0)
                    self.volume_multiplier = settings.get('volume_multiplier', 1.0)
                    
                self.logger.info("🤖 AI Optimizer ayarları yüklendi")
        except Exception as e:
            self.logger.error(f"Optimizer ayarları yüklenirken hata: {e}")
    
    def save_current_settings(self):
        """Mevcut ayarları kaydet"""
        try:
            settings = {
                'min_confidence_threshold': self.min_confidence_threshold,
                'max_signals_per_hour': self.max_signals_per_hour,
                'risk_reward_min': self.risk_reward_min,
                'adx_threshold': self.adx_threshold,
                'volume_multiplier': self.volume_multiplier,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.current_settings, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Optimizer ayarları kaydedilirken hata: {e}")
    
    def record_signal_result(self, signal: Dict, actual_result: Dict):
        """Sinyal sonucunu kaydet"""
        try:
            # M5 confirmation skorunu al
            m5_confirmation_score = 0
            m5_candle_1_score = 0
            m5_candle_2_score = 0
            
            if 'm5_confirmation' in signal:
                m5_confirmation_score = signal['m5_confirmation'].get('confirmation_strength', 0)
                if 'candle_analysis' in signal['m5_confirmation']:
                    candle_analyses = signal['m5_confirmation']['candle_analysis']
                    if len(candle_analyses) >= 2:
                        m5_candle_1_score = candle_analyses[0].get('points', 0)
                        m5_candle_2_score = candle_analyses[1].get('points', 0)
            
            # Sonuç verisi hazırla
            result_data = {
                'timestamp': datetime.now().isoformat(),
                'symbol': signal.get('symbol', 'UNKNOWN'),
                'signal_type': signal.get('signal', 'UNKNOWN'),
                'confidence': signal.get('confidence', 0),
                'entry_price': signal.get('entry_price', 0),
                'take_profit_1': signal.get('take_profit_1', 0),
                'take_profit_2': signal.get('take_profit_2', 0),
                'take_profit_3': signal.get('take_profit_3', 0),
                'stop_loss': signal.get('stop_loss', 0),
                'risk_reward_ratio': signal.get('risk_reward_ratio', 0),
                'strategy': signal.get('reason', 'UNKNOWN'),
                'adx_value': signal.get('adx_value', 0),
                'volume_score': signal.get('volume_score', 0),
                
                # 🚨 YENİ: M5 Confirmation skorları
                'm5_confirmation_score': m5_confirmation_score,
                'm5_candle_1_score': m5_candle_1_score,
                'm5_candle_2_score': m5_candle_2_score,
                
                # Gerçek sonuçlar
                'success': actual_result.get('success', False),
                'profit_loss_percent': actual_result.get('profit_loss_percent', 0),
                'hit_tp1': actual_result.get('hit_tp1', False),
                'hit_tp2': actual_result.get('hit_tp2', False),
                'hit_tp3': actual_result.get('hit_tp3', False),
                'hit_sl': actual_result.get('hit_sl', False),
                'duration_minutes': actual_result.get('duration_minutes', 0),
                'market_condition': actual_result.get('market_condition', 'UNKNOWN')
            }
            
            # Dosyaya kaydet
            performance_data = []
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    performance_data = json.load(f)
            
            performance_data.append(result_data)
            
            # Son 1000 kaydı tut
            if len(performance_data) > 1000:
                performance_data = performance_data[-1000:]
            
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"📊 Sinyal sonucu kaydedildi: {signal.get('symbol')} - {'✅' if actual_result.get('success') else '❌'} (M5: {m5_confirmation_score:.0f}%)")
            
        except Exception as e:
            self.logger.error(f"Sinyal sonucu kaydedilirken hata: {e}")
    
    def analyze_performance(self) -> Dict:
        """Performans analizi yap"""
        try:
            if not os.path.exists(self.performance_file):
                return {"analysis": "Henüz yeterli veri yok"}
            
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if len(data) < 10:
                return {"analysis": "Henüz yeterli veri yok (min 10 sinyal gerekli)"}
            
            df = pd.DataFrame(data)
            
            # Genel istatistikler
            total_signals = len(df)
            success_rate = (df['success'].sum() / total_signals) * 100
            avg_profit = df['profit_loss_percent'].mean()
            total_profit = df['profit_loss_percent'].sum()
            
            # Strateji bazında analiz
            strategy_performance = df.groupby('strategy').agg({
                'success': ['count', 'sum', 'mean'],
                'profit_loss_percent': ['mean', 'sum']
            }).round(2)
            
            # Confidence seviyesi analizi
            high_conf_signals = df[df['confidence'] >= 80]
            medium_conf_signals = df[(df['confidence'] >= 70) & (df['confidence'] < 80)]
            low_conf_signals = df[df['confidence'] < 70]
            
            # Zaman analizi
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            hourly_performance = df.groupby('hour')['success'].mean()
            best_hours = hourly_performance.nlargest(3)
            worst_hours = hourly_performance.nsmallest(3)
            
            analysis = {
                "total_signals": total_signals,
                "success_rate": round(success_rate, 2),
                "avg_profit": round(avg_profit, 2),
                "total_profit": round(total_profit, 2),
                "high_confidence_success": round(high_conf_signals['success'].mean() * 100, 2) if len(high_conf_signals) > 0 else 0,
                "medium_confidence_success": round(medium_conf_signals['success'].mean() * 100, 2) if len(medium_conf_signals) > 0 else 0,
                "low_confidence_success": round(low_conf_signals['success'].mean() * 100, 2) if len(low_conf_signals) > 0 else 0,
                "best_strategy": strategy_performance.loc[strategy_performance[('success', 'mean')].idxmax()].name if len(strategy_performance) > 0 else "Bilinmiyor",
                "worst_strategy": strategy_performance.loc[strategy_performance[('success', 'mean')].idxmin()].name if len(strategy_performance) > 0 else "Bilinmiyor",
                "best_hours": best_hours.to_dict(),
                "worst_hours": worst_hours.to_dict(),
                "recommendation": self.generate_recommendations(df)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Performans analizi hatası: {e}")
            return {"analysis": f"Analiz hatası: {e}"}
    
    def generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """AI tabanlı öneriler üret"""
        recommendations = []
        
        try:
            # Confidence threshold analizi
            high_conf = df[df['confidence'] >= 80]['success'].mean()
            med_conf = df[(df['confidence'] >= 70) & (df['confidence'] < 80)]['success'].mean()
            
            if high_conf > med_conf + 0.15:  # %15 daha başarılı
                recommendations.append("🎯 Confidence threshold'u 80'e yükselt - yüksek güvenli sinyaller daha başarılı")
                self.min_confidence_threshold = min(80.0, self.min_confidence_threshold + 2.0)
            
            # Risk/Reward analizi
            high_rr = df[df['risk_reward_ratio'] >= 2.0]['success'].mean()
            low_rr = df[df['risk_reward_ratio'] < 2.0]['success'].mean()
            
            if high_rr > low_rr + 0.1:
                recommendations.append("💎 Risk/Reward oranını minimum 2.0'a çıkar")
                self.risk_reward_min = max(2.0, self.risk_reward_min + 0.1)
            
            # ADX analizi
            high_adx = df[df['adx_value'] >= 30]['success'].mean()
            low_adx = df[df['adx_value'] < 30]['success'].mean()
            
            if high_adx > low_adx + 0.1:
                recommendations.append("⚡ ADX threshold'u 30'a yükselt - güçlü trend gerekli")
                self.adx_threshold = min(35.0, self.adx_threshold + 1.0)
            
            # Zaman analizi
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            night_success = df[df['hour'].isin([22, 23, 0, 1, 2, 3, 4, 5])]['success'].mean()
            day_success = df[~df['hour'].isin([22, 23, 0, 1, 2, 3, 4, 5])]['success'].mean()
            
            if day_success > night_success + 0.15:
                recommendations.append("🕐 Gece saatlerinde daha az sinyal ver (22:00-06:00)")
            
            # Strateji analizi
            strategy_performance = df.groupby('strategy')['success'].mean()
            if len(strategy_performance) > 1:
                best_strategy = strategy_performance.idxmax()
                worst_strategy = strategy_performance.idxmin()
                
                if strategy_performance[best_strategy] > strategy_performance[worst_strategy] + 0.2:
                    recommendations.append(f"🎯 {best_strategy} stratejisine öncelik ver, {worst_strategy} stratejisini azalt")
            
            # Genel başarı oranı kontrolü
            overall_success = df['success'].mean()
            if overall_success < 0.6:  # %60'ın altında
                recommendations.append("⚠️ Genel başarı oranı düşük - tüm parametreleri sıkılaştır")
                self.min_confidence_threshold = min(85.0, self.min_confidence_threshold + 5.0)
                self.max_signals_per_hour = max(6, self.max_signals_per_hour - 2)
            elif overall_success > 0.8:  # %80'in üstünde
                recommendations.append("🚀 Başarı oranı yüksek - daha fazla sinyal verebiliriz")
                self.max_signals_per_hour = min(20, self.max_signals_per_hour + 2)
            
            # Ayarları kaydet
            self.save_current_settings()
            
            if not recommendations:
                recommendations.append("✅ Mevcut parametreler optimal görünüyor")
                
        except Exception as e:
            self.logger.error(f"Öneri üretme hatası: {e}")
            recommendations.append(f"❌ Öneri analizi hatası: {e}")
        
        return recommendations
    
    def should_send_signal(self, signal: Dict) -> tuple[bool, str]:
        """Sinyalin gönderilip gönderilmeyeceğini AI ile karar ver"""
        try:
            # Temel filtreleme
            confidence = signal.get('confidence', 0)
            risk_reward = signal.get('risk_reward_ratio', 0)
            
            if confidence < self.min_confidence_threshold:
                return False, f"Düşük confidence: {confidence}% < {self.min_confidence_threshold}%"
            
            if risk_reward < self.risk_reward_min:
                return False, f"Düşük R/R: {risk_reward} < {self.risk_reward_min}"
            
            # Saatlik sinyal limitı kontrolü
            # Bu kısım main.py'de yapılmalı
            
            return True, "✅ AI onayı alındı"
            
        except Exception as e:
            self.logger.error(f"Sinyal filtreleme hatası: {e}")
            return True, "Filtreleme hatası - sinyal geçti"
    
    def get_optimized_parameters(self) -> Dict:
        """Optimize edilmiş parametreleri döndür"""
        return {
            'min_confidence_threshold': self.min_confidence_threshold,
            'max_signals_per_hour': self.max_signals_per_hour,
            'risk_reward_min': self.risk_reward_min,
            'adx_threshold': self.adx_threshold,
            'volume_multiplier': self.volume_multiplier
        }
    
    def generate_performance_report(self) -> str:
        """Performans raporu oluştur"""
        try:
            analysis = self.analyze_performance()
            
            if "analysis" in analysis and "yeterli veri yok" in analysis["analysis"]:
                return "📊 **AI Optimizer Raporu**\n\n⏳ Henüz yeterli veri biriktirilmedi. En az 10 sinyal gerekli."
            
            report = f"""
📊 **AI OPTIMIZER PERFORMANS RAPORU**
=====================================

📈 **Genel İstatistikler:**
• Toplam Sinyal: {analysis['total_signals']}
• Başarı Oranı: %{analysis['success_rate']}
• Ortalama Kar: %{analysis['avg_profit']}
• Toplam Kar: %{analysis['total_profit']}

🎯 **Confidence Analizi:**
• Yüksek Güven (≥80%): %{analysis['high_confidence_success']} başarı
• Orta Güven (70-80%): %{analysis['medium_confidence_success']} başarı  
• Düşük Güven (<70%): %{analysis['low_confidence_success']} başarı

🚀 **Strateji Performansı:**
• En Başarılı: {analysis['best_strategy']}
• En Başarısız: {analysis['worst_strategy']}

⏰ **Zaman Analizi:**
• En İyi Saatler: {', '.join([f'{h}:00' for h in list(analysis['best_hours'].keys())[:3]])}
• En Kötü Saatler: {', '.join([f'{h}:00' for h in list(analysis['worst_hours'].keys())[:3]])}

🤖 **AI Önerileri:**
"""
            
            for i, rec in enumerate(analysis['recommendation'], 1):
                report += f"{i}. {rec}\n"
            
            report += f"\n⚙️ **Güncel Parametreler:**\n"
            report += f"• Min Confidence: {self.min_confidence_threshold}%\n"
            report += f"• Max Sinyal/Saat: {self.max_signals_per_hour}\n"
            report += f"• Min R/R Oranı: {self.risk_reward_min}\n"
            report += f"• ADX Threshold: {self.adx_threshold}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Rapor oluşturma hatası: {e}")
            return f"❌ Rapor oluşturulamadı: {e}"
    
    def analyze_stop_loss_patterns(self, signal: Dict, result: Dict):
        """Stop Loss pattern analizi - AI kendini geliştirsin"""
        try:
            if not result.get('hit_sl', False):
                return
            
            stop_loss_reason = result.get('stop_loss_reason', 'Unknown')
            symbol = signal.get('symbol', 'UNKNOWN')
            strategy = signal.get('reason', 'UNKNOWN')
            
            # SL nedenlerine göre ayarlamaları yap
            if 'Güçlü tersine hareket' in stop_loss_reason:
                # ADX threshold'unu yükselt
                self.adx_threshold = min(35.0, self.adx_threshold + 1.0)
                self.logger.info(f"🤖 Güçlü tersine hareket nedeniyle ADX threshold yükseltildi: {self.adx_threshold}")
                
            elif 'Trend değişimi' in stop_loss_reason:
                # Confidence threshold'unu yükselt
                self.min_confidence_threshold = min(85.0, self.min_confidence_threshold + 2.0)
                self.logger.info(f"🤖 Trend değişimi nedeniyle confidence threshold yükseltildi: {self.min_confidence_threshold}")
                
            elif 'Düzeltme hareketi' in stop_loss_reason:
                # Risk/Reward oranını artır
                self.risk_reward_min = min(2.5, self.risk_reward_min + 0.1)
                self.logger.info(f"🤖 Düzeltme hareketi nedeniyle R/R oranı artırıldı: {self.risk_reward_min}")
                
            # SMC stratejisi için özel ayarlamalar
            if 'SMC' in strategy:
                if result.get('duration_minutes', 0) < 30:  # Çok erken SL
                    self.logger.info(f"🤖 SMC stratejisinde erken SL: {symbol} - Daha sıkı filtreler uygulanacak")
                    # SMC için daha sıkı koşullar
                    
            # Momentum stratejisi için özel ayarlamalar
            elif 'MOM' in strategy:
                if result.get('duration_minutes', 0) < 15:  # Çok erken SL
                    self.logger.info(f"🤖 Momentum stratejisinde erken SL: {symbol} - Momentum filtreleri sıkılaştırılacak")
            
            # Ayarları kaydet
            self.save_current_settings()
            
            # SL pattern log'u
            pattern_log = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'strategy': strategy,
                'sl_reason': stop_loss_reason,
                'duration_minutes': result.get('duration_minutes', 0),
                'new_adx_threshold': self.adx_threshold,
                'new_confidence_threshold': self.min_confidence_threshold,
                'new_risk_reward_min': self.risk_reward_min
            }
            
            # SL pattern dosyasına kaydet
            self._save_sl_pattern(pattern_log)
            
        except Exception as e:
            self.logger.error(f"SL pattern analizi hatası: {e}")
    
    def _save_sl_pattern(self, pattern_log: Dict):
        """SL pattern'ını dosyaya kaydet"""
        try:
            sl_patterns_file = "data/sl_patterns.json"
            patterns = []
            
            if os.path.exists(sl_patterns_file):
                with open(sl_patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
            
            patterns.append(pattern_log)
            
            # Son 500 kaydı tut
            if len(patterns) > 500:
                patterns = patterns[-500:]
            
            with open(sl_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"SL pattern kaydetme hatası: {e}")
    
    def analyze_m5_confirmation_performance(self) -> Dict:
        """M5 confirmation sisteminin performansını analiz et"""
        try:
            if not os.path.exists(self.performance_file):
                return {'status': 'error', 'message': 'Henüz veri yok'}
            
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # M5 confirmation'lı sinyalleri filtrele
            m5_signals = [d for d in data if d.get('m5_confirmation_score', 0) > 0]
            
            if len(m5_signals) < 5:
                return {'status': 'insufficient_data', 'message': f'M5 onaylı sadece {len(m5_signals)} sinyal var'}
            
            # Analiz sonuçları
            total_signals = len(m5_signals)
            successful_signals = len([d for d in m5_signals if d.get('success', False)])
            success_rate = (successful_signals / total_signals) * 100
            
            # M5 skor aralıklarına göre başarı oranları
            score_ranges = {
                '60-70%': [d for d in m5_signals if 60 <= d.get('m5_confirmation_score', 0) < 70],
                '70-80%': [d for d in m5_signals if 70 <= d.get('m5_confirmation_score', 0) < 80],
                '80-90%': [d for d in m5_signals if 80 <= d.get('m5_confirmation_score', 0) < 90],
                '90-100%': [d for d in m5_signals if 90 <= d.get('m5_confirmation_score', 0) <= 100]
            }
            
            range_analysis = {}
            for range_name, signals in score_ranges.items():
                if len(signals) > 0:
                    range_success = len([s for s in signals if s.get('success', False)])
                    range_analysis[range_name] = {
                        'total': len(signals),
                        'successful': range_success,
                        'success_rate': (range_success / len(signals)) * 100,
                        'avg_profit': sum(s.get('profit_loss_percent', 0) for s in signals) / len(signals)
                    }
            
            # En iyi mum kombinasyonları
            candle_combos = {}
            for signal in m5_signals:
                c1_score = signal.get('m5_candle_1_score', 0)
                c2_score = signal.get('m5_candle_2_score', 0)
                combo_key = f"{c1_score}/{c2_score}"
                
                if combo_key not in candle_combos:
                    candle_combos[combo_key] = {'total': 0, 'successful': 0, 'profits': []}
                
                candle_combos[combo_key]['total'] += 1
                if signal.get('success', False):
                    candle_combos[combo_key]['successful'] += 1
                candle_combos[combo_key]['profits'].append(signal.get('profit_loss_percent', 0))
            
            # En iyi kombinasyonları sırala
            best_combos = []
            for combo, stats in candle_combos.items():
                if stats['total'] >= 3:  # En az 3 sinyal olmalı
                    success_rate_combo = (stats['successful'] / stats['total']) * 100
                    avg_profit = sum(stats['profits']) / len(stats['profits'])
                    best_combos.append({
                        'combo': combo,
                        'success_rate': success_rate_combo,
                        'avg_profit': avg_profit,
                        'total_signals': stats['total']
                    })
            
            best_combos.sort(key=lambda x: (x['success_rate'], x['avg_profit']), reverse=True)
            
            result = {
                'status': 'success',
                'total_m5_signals': total_signals,
                'overall_success_rate': success_rate,
                'score_range_analysis': range_analysis,
                'best_candle_combinations': best_combos[:5],  # Top 5
                'recommendations': []
            }
            
            # Öneriler
            if success_rate > 70:
                result['recommendations'].append("✅ M5 confirmation sistemi başarılı çalışıyor")
            else:
                result['recommendations'].append("⚠️ M5 confirmation minimum skorunu artırmayı düşünün")
            
            # En iyi skor aralığını bul
            if range_analysis:
                best_range = max(range_analysis.items(), key=lambda x: x[1]['success_rate'])
                result['recommendations'].append(f"🎯 En iyi performans: {best_range[0]} aralığında")
            
            return result
            
        except Exception as e:
            self.logger.error(f"M5 analizi hatası: {e}")
            return {'status': 'error', 'message': str(e)}
    
    # 🚀 YENİ: GELİŞMİŞ STRATEJİ OPTİMİZASYONU
    def __init_advanced_params(self):
        """Gelişmiş strateji parametrelerini başlat"""
        # SMC Strategy Parameters
        self.smc_entry_precision = 0.8  # Entry hassasiyeti (0.5-1.0)
        self.smc_confirmation_min = 60   # M5 minimum confirmation %
        self.smc_risk_reward_ratio = 1.5 # R/R oranı
        
        # Take Profit Ayarları
        self.tp1_distance_multiplier = 1.0  # TP1 mesafe çarpanı
        self.tp2_distance_multiplier = 2.0  # TP2 mesafe çarpanı  
        self.tp3_distance_multiplier = 3.0  # TP3 mesafe çarpanı
        
        # Stop Loss Ayarları
        self.sl_atr_multiplier = 1.5       # ATR çarpanı (1.0-3.0)
        self.sl_percentage_max = 2.0        # Maximum SL % (1.0-5.0)
        
        # Order Block & FVG Ayarları
        self.ob_strength_min = 70           # OB minimum güç
        self.fvg_size_min = 0.5            # FVG minimum boyut %
        
        # Volume Analysis
        self.volume_threshold_multiplier = 1.5  # Hacim eşik çarpanı
        
        # Liquidity Sweep Settings
        self.liquidity_sweep_tolerance = 0.2    # Likidite sweep toleransı %
        
    def optimize_strategy_parameters(self, failed_signals: list, market_conditions: dict):
        """
        🤖 AI Gelişmiş Strateji Optimizasyonu
        Başarısız sinyallere göre tüm strateji parametrelerini optimize eder
        """
        try:
            self.logger.info("🤖 AI Gelişmiş Strateji Optimizasyonu başlıyor...")
            
            if not hasattr(self, 'smc_entry_precision'):
                self.__init_advanced_params()
            
            optimizations = []
            
            # 1. ENTRY PRECİSİON OPTİMİZASYONU
            entry_optimization = self._optimize_entry_precision(failed_signals)
            if entry_optimization['changed']:
                optimizations.append(entry_optimization)
            
            # 2. TAKE PROFIT OPTİMİZASYONU
            tp_optimization = self._optimize_take_profits(failed_signals)
            if tp_optimization['changed']:
                optimizations.append(tp_optimization)
            
            # 3. STOP LOSS OPTİMİZASYONU
            sl_optimization = self._optimize_stop_loss(failed_signals)
            if sl_optimization['changed']:
                optimizations.append(sl_optimization)
            
            # 4. SMC KONFİRMASYON OPTİMİZASYONU
            smc_optimization = self._optimize_smc_confirmation(failed_signals)
            if smc_optimization['changed']:
                optimizations.append(smc_optimization)
            
            # 5. ORDER BLOCK & FVG OPTİMİZASYONU
            ob_fvg_optimization = self._optimize_ob_fvg(failed_signals)
            if ob_fvg_optimization['changed']:
                optimizations.append(ob_fvg_optimization)
            
            # 6. VOLUME ANALİZ OPTİMİZASYONU
            volume_optimization = self._optimize_volume_analysis(failed_signals)
            if volume_optimization['changed']:
                optimizations.append(volume_optimization)
            
            # 7. LİKİDİTE SWEEP OPTİMİZASYONU
            liquidity_optimization = self._optimize_liquidity_sweep(failed_signals)
            if liquidity_optimization['changed']:
                optimizations.append(liquidity_optimization)
            
            # Tüm optimizasyonları kaydet
            if optimizations:
                self._save_advanced_settings()
                
                optimization_summary = {
                    'timestamp': datetime.now().isoformat(),
                    'total_failed_signals': len(failed_signals),
                    'optimizations_applied': len(optimizations),
                    'optimizations': optimizations,
                    'market_conditions': market_conditions
                }
                
                self._save_optimization_log(optimization_summary)
                
                self.logger.info(f"🤖 AI {len(optimizations)} parametre optimizasyonu uyguladı!")
                
                return {
                    'success': True,
                    'optimizations_count': len(optimizations),
                    'optimizations': optimizations,
                    'message': f"AI {len(optimizations)} strateji parametresini optimize etti!"
                }
            else:
                self.logger.info("🤖 AI mevcut parametrelerin optimal olduğunu belirledi")
                return {
                    'success': True,
                    'optimizations_count': 0,
                    'message': "Mevcut parametreler optimal durumda"
                }
                
        except Exception as e:
            self.logger.error(f"Gelişmiş optimizasyon hatası: {e}")
            return {'success': False, 'error': str(e)}
    
    def _optimize_entry_precision(self, failed_signals: list) -> dict:
        """Entry precision optimizasyonu"""
        try:
            early_entries = [s for s in failed_signals if 'early_entry' in s.get('failure_reason', '')]
            late_entries = [s for s in failed_signals if 'late_entry' in s.get('failure_reason', '')]
            
            old_precision = self.smc_entry_precision
            
            if len(early_entries) > len(late_entries):
                # Çok erken giriş yapıyoruz, hassasiyeti artır
                self.smc_entry_precision = min(1.0, self.smc_entry_precision + 0.1)
            elif len(late_entries) > len(early_entries):
                # Çok geç giriş yapıyoruz, hassasiyeti azalt
                self.smc_entry_precision = max(0.5, self.smc_entry_precision - 0.1)
            
            return {
                'parameter': 'entry_precision',
                'old_value': old_precision,
                'new_value': self.smc_entry_precision,
                'changed': old_precision != self.smc_entry_precision,
                'reason': f"Early entries: {len(early_entries)}, Late entries: {len(late_entries)}"
            }
            
        except Exception as e:
            return {'parameter': 'entry_precision', 'error': str(e), 'changed': False}
    
    def _optimize_take_profits(self, failed_signals: list) -> dict:
        """Take Profit optimizasyonu"""
        try:
            tp_missed = [s for s in failed_signals if 'tp_missed' in s.get('failure_reason', '')]
            tp_too_close = [s for s in failed_signals if 'tp_too_close' in s.get('failure_reason', '')]
            
            old_tp1 = self.tp1_distance_multiplier
            old_tp2 = self.tp2_distance_multiplier
            old_tp3 = self.tp3_distance_multiplier
            
            if len(tp_missed) > 3:
                # TP'ler çok uzak, yakınlaştır
                self.tp1_distance_multiplier = max(0.8, self.tp1_distance_multiplier - 0.1)
                self.tp2_distance_multiplier = max(1.5, self.tp2_distance_multiplier - 0.2)
                self.tp3_distance_multiplier = max(2.0, self.tp3_distance_multiplier - 0.3)
            elif len(tp_too_close) > 3:
                # TP'ler çok yakın, uzaklaştır
                self.tp1_distance_multiplier = min(1.5, self.tp1_distance_multiplier + 0.1)
                self.tp2_distance_multiplier = min(3.0, self.tp2_distance_multiplier + 0.2)
                self.tp3_distance_multiplier = min(4.0, self.tp3_distance_multiplier + 0.3)
            
            changed = (old_tp1 != self.tp1_distance_multiplier or 
                      old_tp2 != self.tp2_distance_multiplier or 
                      old_tp3 != self.tp3_distance_multiplier)
            
            return {
                'parameter': 'take_profits',
                'old_values': {'tp1': old_tp1, 'tp2': old_tp2, 'tp3': old_tp3},
                'new_values': {'tp1': self.tp1_distance_multiplier, 'tp2': self.tp2_distance_multiplier, 'tp3': self.tp3_distance_multiplier},
                'changed': changed,
                'reason': f"TP missed: {len(tp_missed)}, TP too close: {len(tp_too_close)}"
            }
            
        except Exception as e:
            return {'parameter': 'take_profits', 'error': str(e), 'changed': False}
    
    def _optimize_stop_loss(self, failed_signals: list) -> dict:
        """Stop Loss optimizasyonu"""
        try:
            sl_hit = [s for s in failed_signals if 'stop_loss_hit' in s.get('failure_reason', '')]
            sl_too_tight = [s for s in failed_signals if 'sl_too_tight' in s.get('failure_reason', '')]
            
            old_atr = self.sl_atr_multiplier
            old_max = self.sl_percentage_max
            
            if len(sl_hit) > 5:
                # SL çok dar, genişlet
                self.sl_atr_multiplier = min(3.0, self.sl_atr_multiplier + 0.2)
                self.sl_percentage_max = min(5.0, self.sl_percentage_max + 0.3)
            elif len(sl_too_tight) > 3:
                # SL çok geniş, daralt
                self.sl_atr_multiplier = max(1.0, self.sl_atr_multiplier - 0.1)
                self.sl_percentage_max = max(1.0, self.sl_percentage_max - 0.2)
            
            changed = (old_atr != self.sl_atr_multiplier or old_max != self.sl_percentage_max)
            
            return {
                'parameter': 'stop_loss',
                'old_values': {'atr_multiplier': old_atr, 'max_percentage': old_max},
                'new_values': {'atr_multiplier': self.sl_atr_multiplier, 'max_percentage': self.sl_percentage_max},
                'changed': changed,
                'reason': f"SL hit: {len(sl_hit)}, SL too tight: {len(sl_too_tight)}"
            }
            
        except Exception as e:
            return {'parameter': 'stop_loss', 'error': str(e), 'changed': False}
    
    def _optimize_smc_confirmation(self, failed_signals: list) -> dict:
        """SMC Confirmation optimizasyonu"""
        try:
            weak_confirmation = [s for s in failed_signals if s.get('m5_confirmation_score', 100) < 60]
            
            old_min = self.smc_confirmation_min
            old_rr = self.smc_risk_reward_ratio
            
            if len(weak_confirmation) > 3:
                # Zayıf konfirmasyonlar çok, eşikleri artır
                self.smc_confirmation_min = min(80, self.smc_confirmation_min + 5)
                self.smc_risk_reward_ratio = min(2.5, self.smc_risk_reward_ratio + 0.1)
            
            changed = (old_min != self.smc_confirmation_min or old_rr != self.smc_risk_reward_ratio)
            
            return {
                'parameter': 'smc_confirmation',
                'old_values': {'min_confirmation': old_min, 'risk_reward': old_rr},
                'new_values': {'min_confirmation': self.smc_confirmation_min, 'risk_reward': self.smc_risk_reward_ratio},
                'changed': changed,
                'reason': f"Weak confirmations: {len(weak_confirmation)}"
            }
            
        except Exception as e:
            return {'parameter': 'smc_confirmation', 'error': str(e), 'changed': False}
    
    def _optimize_ob_fvg(self, failed_signals: list) -> dict:
        """Order Block & FVG optimizasyonu"""
        try:
            weak_ob = [s for s in failed_signals if 'weak_order_block' in s.get('failure_reason', '')]
            small_fvg = [s for s in failed_signals if 'small_fvg' in s.get('failure_reason', '')]
            
            old_ob = self.ob_strength_min
            old_fvg = self.fvg_size_min
            
            if len(weak_ob) > 2:
                self.ob_strength_min = min(90, self.ob_strength_min + 5)
            
            if len(small_fvg) > 2:
                self.fvg_size_min = min(1.0, self.fvg_size_min + 0.1)
            
            changed = (old_ob != self.ob_strength_min or old_fvg != self.fvg_size_min)
            
            return {
                'parameter': 'ob_fvg',
                'old_values': {'ob_strength': old_ob, 'fvg_size': old_fvg},
                'new_values': {'ob_strength': self.ob_strength_min, 'fvg_size': self.fvg_size_min},
                'changed': changed,
                'reason': f"Weak OB: {len(weak_ob)}, Small FVG: {len(small_fvg)}"
            }
            
        except Exception as e:
            return {'parameter': 'ob_fvg', 'error': str(e), 'changed': False}
    
    def _optimize_volume_analysis(self, failed_signals: list) -> dict:
        """Volume Analysis optimizasyonu"""
        try:
            low_volume = [s for s in failed_signals if 'low_volume' in s.get('failure_reason', '')]
            
            old_volume = self.volume_threshold_multiplier
            
            if len(low_volume) > 4:
                # Düşük hacim çok, eşiği artır
                self.volume_threshold_multiplier = min(3.0, self.volume_threshold_multiplier + 0.2)
            
            changed = old_volume != self.volume_threshold_multiplier
            
            return {
                'parameter': 'volume_analysis',
                'old_value': old_volume,
                'new_value': self.volume_threshold_multiplier,
                'changed': changed,
                'reason': f"Low volume signals: {len(low_volume)}"
            }
            
        except Exception as e:
            return {'parameter': 'volume_analysis', 'error': str(e), 'changed': False}
    
    def _optimize_liquidity_sweep(self, failed_signals: list) -> dict:
        """Liquidity Sweep optimizasyonu"""
        try:
            false_sweeps = [s for s in failed_signals if 'false_liquidity_sweep' in s.get('failure_reason', '')]
            
            old_tolerance = self.liquidity_sweep_tolerance
            
            if len(false_sweeps) > 2:
                # Yanlış sweep'ler çok, toleransı azalt
                self.liquidity_sweep_tolerance = max(0.1, self.liquidity_sweep_tolerance - 0.05)
            
            changed = old_tolerance != self.liquidity_sweep_tolerance
            
            return {
                'parameter': 'liquidity_sweep',
                'old_value': old_tolerance,
                'new_value': self.liquidity_sweep_tolerance,
                'changed': changed,
                'reason': f"False sweeps: {len(false_sweeps)}"
            }
            
        except Exception as e:
            return {'parameter': 'liquidity_sweep', 'error': str(e), 'changed': False}
    
    def _save_advanced_settings(self):
        """Gelişmiş ayarları kaydet"""
        try:
            if not hasattr(self, 'smc_entry_precision'):
                return
                
            advanced_settings = {
                # Ana parametreler
                'min_confidence_threshold': self.min_confidence_threshold,
                'max_signals_per_hour': self.max_signals_per_hour,
                'risk_reward_min': self.risk_reward_min,
                'adx_threshold': self.adx_threshold,
                'volume_multiplier': self.volume_multiplier,
                
                # Gelişmiş SMC parametreleri
                'smc_entry_precision': self.smc_entry_precision,
                'smc_confirmation_min': self.smc_confirmation_min,
                'smc_risk_reward_ratio': self.smc_risk_reward_ratio,
                
                # Take Profit ayarları
                'tp1_distance_multiplier': self.tp1_distance_multiplier,
                'tp2_distance_multiplier': self.tp2_distance_multiplier,
                'tp3_distance_multiplier': self.tp3_distance_multiplier,
                
                # Stop Loss ayarları
                'sl_atr_multiplier': self.sl_atr_multiplier,
                'sl_percentage_max': self.sl_percentage_max,
                
                # Order Block & FVG
                'ob_strength_min': self.ob_strength_min,
                'fvg_size_min': self.fvg_size_min,
                
                # Volume & Liquidity
                'volume_threshold_multiplier': self.volume_threshold_multiplier,
                'liquidity_sweep_tolerance': self.liquidity_sweep_tolerance,
                
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.current_settings, 'w', encoding='utf-8') as f:
                json.dump(advanced_settings, f, indent=2, ensure_ascii=False)
                
            self.logger.info("🤖 Gelişmiş AI ayarları kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Gelişmiş ayarları kaydetme hatası: {e}")
    
    def get_optimized_parameters(self) -> dict:
        """Optimize edilmiş parametreleri döndür"""
        if not hasattr(self, 'smc_entry_precision'):
            self.__init_advanced_params()
            
        return {
            'smc': {
                'entry_precision': self.smc_entry_precision,
                'confirmation_min': self.smc_confirmation_min,
                'risk_reward_ratio': self.smc_risk_reward_ratio
            },
            'take_profits': {
                'tp1_multiplier': self.tp1_distance_multiplier,
                'tp2_multiplier': self.tp2_distance_multiplier,
                'tp3_multiplier': self.tp3_distance_multiplier
            },
            'stop_loss': {
                'atr_multiplier': self.sl_atr_multiplier,
                'max_percentage': self.sl_percentage_max
            },
            'order_blocks': {
                'strength_min': self.ob_strength_min,
                'fvg_size_min': self.fvg_size_min
            },
            'volume': {
                'threshold_multiplier': self.volume_threshold_multiplier
            },
            'liquidity': {
                'sweep_tolerance': self.liquidity_sweep_tolerance
            },
            'general': {
                'adx_threshold': self.adx_threshold,
                'confidence_min': self.min_confidence_threshold,
                'volume_multiplier': self.volume_multiplier
            }
        }
    
    def _save_optimization_log(self, optimization_data: dict):
        """Optimizasyon logunu kaydet"""
        try:
            log_file = "data/ai_optimization_log.json"
            
            # Mevcut logu oku
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Yeni log ekle
            logs.append(optimization_data)
            
            # Son 100 log kayıt tut
            if len(logs) > 100:
                logs = logs[-100:]
            
            # Kaydet
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Optimizasyon logu kaydetme hatası: {e}")
    
    # 🚀 PERFORMANS TAKİP SİSTEMİ
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