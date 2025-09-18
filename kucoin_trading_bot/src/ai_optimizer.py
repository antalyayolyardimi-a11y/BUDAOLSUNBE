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