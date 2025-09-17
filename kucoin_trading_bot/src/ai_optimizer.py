import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class AIOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.feature_columns = [
            'rsi', 'macd_histogram', 'bb_position', 'trend_strength', 
            'volume_ratio', 'price_change_1h', 'volume_change_1h'
        ]
        self.signal_history = []
        self.performance_data = []
        
    def analyze_signal_performance(self, signal: Dict, outcome: Dict) -> Dict:
        """Sinyal performansını analiz et"""
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            take_profits = signal['take_profits']
            signal_type = signal['signal_type']
            
            # Sonuç analizi
            result = {
                'signal_id': outcome.get('signal_id', ''),
                'symbol': signal['symbol'],
                'signal_type': signal_type,
                'entry_price': entry_price,
                'exit_price': outcome.get('exit_price', entry_price),
                'exit_reason': outcome.get('exit_reason', 'unknown'),
                'profit_loss': 0,
                'profit_percentage': 0,
                'hit_tp_level': outcome.get('hit_tp_level', 0),
                'max_drawdown': outcome.get('max_drawdown', 0),
                'duration_minutes': outcome.get('duration_minutes', 0),
                'signal_strength': signal['signal_strength'],
                'confidence': signal['confidence'],
                'timestamp': outcome.get('timestamp', datetime.now().isoformat())
            }
            
            # Kar/Zarar hesaplama
            exit_price = outcome.get('exit_price', entry_price)
            if signal_type == 'LONG':
                result['profit_loss'] = exit_price - entry_price
                result['profit_percentage'] = ((exit_price - entry_price) / entry_price) * 100
            else:  # SHORT
                result['profit_loss'] = entry_price - exit_price
                result['profit_percentage'] = ((entry_price - exit_price) / entry_price) * 100
                
            # Başarı durumu
            result['is_successful'] = result['profit_percentage'] > 0
            
            # TP seviye skoru
            tp_score = 0
            if result['hit_tp_level'] >= 1:
                tp_score += 1
            if result['hit_tp_level'] >= 2:
                tp_score += 2
            if result['hit_tp_level'] >= 3:
                tp_score += 3
            result['tp_score'] = tp_score
            
            self.performance_data.append(result)
            
            # Performans verilerini kaydet
            self._save_performance_data()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sinyal performans analizi hatası: {e}")
            return {}
            
    def analyze_stop_loss_reasons(self, failed_signals: List[Dict]) -> Dict:
        """Stop loss nedenlerini analiz et"""
        reasons = {
            'trend_reversal': 0,
            'volume_drop': 0,
            'market_wide_drop': 0,
            'false_breakout': 0,
            'news_impact': 0,
            'technical_failure': 0
        }
        
        detailed_analysis = []
        
        for signal in failed_signals:
            analysis = signal.get('analysis', {})
            indicators = analysis.get('indicators', {})
            
            # Trend tersine dönüş kontrolü
            if self._detect_trend_reversal(analysis):
                reasons['trend_reversal'] += 1
                
            # Volume düşüş kontrolü
            if self._detect_volume_drop(indicators):
                reasons['volume_drop'] += 1
                
            # False breakout kontrolü
            if self._detect_false_breakout(analysis):
                reasons['false_breakout'] += 1
                
            # Teknik analiz başarısızlığı
            if self._detect_technical_failure(indicators):
                reasons['technical_failure'] += 1
                
            detailed_analysis.append({
                'symbol': signal['symbol'],
                'reasons': self._get_specific_failure_reasons(analysis),
                'lesson_learned': self._generate_lesson(analysis)
            })
            
        return {
            'summary': reasons,
            'detailed_analysis': detailed_analysis,
            'recommendations': self._generate_optimization_recommendations(reasons)
        }
        
    def _detect_trend_reversal(self, analysis: Dict) -> bool:
        """Trend tersine dönüş tespit et"""
        trend = analysis.get('trend', {})
        adx = trend.get('adx', 0)
        trend_direction = trend.get('trend_direction', 0)
        
        # Zayıf trend ve belirsiz yön
        return adx < 20 and trend_direction == 0
        
    def _detect_volume_drop(self, indicators: Dict) -> bool:
        """Volume düşüş tespit et"""
        volume = indicators.get('volume', {})
        cmf = volume.get('cmf', 0)
        
        return cmf < -0.2
        
    def _detect_false_breakout(self, analysis: Dict) -> bool:
        """False breakout tespit et"""
        indicators = analysis.get('indicators', {})
        bb = indicators.get('bollinger_bands', {})
        bb_position = bb.get('position', 0.5)
        
        # BB dışında ama hızla geri dönen
        return bb_position > 0.9 or bb_position < 0.1
        
    def _detect_technical_failure(self, indicators: Dict) -> bool:
        """Teknik analiz başarısızlığı tespit et"""
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', {})
        macd_histogram = macd.get('histogram', 0)
        
        # Çelişkili sinyaller
        return (rsi > 70 and macd_histogram > 0) or (rsi < 30 and macd_histogram < 0)
        
    def _get_specific_failure_reasons(self, analysis: Dict) -> List[str]:
        """Spesifik başarısızlık nedenlerini belirle"""
        reasons = []
        
        if self._detect_trend_reversal(analysis):
            reasons.append("Zayıf trend gücü - ADX < 20")
            
        if self._detect_volume_drop(analysis.get('indicators', {})):
            reasons.append("Volume konfirmasyonu eksik - CMF negatif")
            
        if self._detect_false_breakout(analysis):
            reasons.append("False breakout - BB ekstrem pozisyon")
            
        if self._detect_technical_failure(analysis.get('indicators', {})):
            reasons.append("Çelişkili teknik sinyaller")
            
        return reasons
        
    def _generate_lesson(self, analysis: Dict) -> str:
        """Analiz sonucundan ders çıkar"""
        lessons = []
        
        trend = analysis.get('trend', {})
        if trend.get('adx', 0) < 25:
            lessons.append("Güçlü trend olmadan sinyal verme")
            
        indicators = analysis.get('indicators', {})
        volume = indicators.get('volume', {})
        if volume.get('cmf', 0) < 0:
            lessons.append("Volume konfirmasyonu olmadan işlem yapma")
            
        if not lessons:
            lessons.append("Risk yönetimini geliştir")
            
        return "; ".join(lessons)
        
    def _generate_optimization_recommendations(self, reasons: Dict) -> List[str]:
        """Optimizasyon önerileri üret"""
        recommendations = []
        total_failures = sum(reasons.values())
        
        if total_failures == 0:
            return ["Mevcut ayarlar optimal görünüyor"]
            
        # En sık görülen hata nedenleri için öneriler
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        
        for reason, count in sorted_reasons[:3]:
            percentage = (count / total_failures) * 100
            
            if reason == 'trend_reversal' and percentage > 30:
                recommendations.append("ADX filtresi ekle - minimum 25")
                
            elif reason == 'volume_drop' and percentage > 25:
                recommendations.append("CMF pozitif gereksinimi ekle")
                
            elif reason == 'false_breakout' and percentage > 20:
                recommendations.append("BB pozisyon filtresi güçlendir")
                
            elif reason == 'technical_failure' and percentage > 15:
                recommendations.append("Çelişkili sinyal filtresi ekle")
                
        return recommendations
        
    def optimize_parameters(self) -> Dict:
        """Parametreleri optimize et"""
        if len(self.performance_data) < 50:
            return {"message": "Yeterli veri yok - minimum 50 sinyal gerekli"}
            
        try:
            # Performans verilerini DataFrame'e çevir
            df = pd.DataFrame(self.performance_data)
            
            # Başarı oranı analizi
            success_rate = df['is_successful'].mean() * 100
            avg_profit = df[df['is_successful']]['profit_percentage'].mean()
            avg_loss = df[~df['is_successful']]['profit_percentage'].mean()
            
            # Sinyal türü analizi
            long_performance = df[df['signal_type'] == 'LONG']['is_successful'].mean() * 100
            short_performance = df[df['signal_type'] == 'SHORT']['is_successful'].mean() * 100
            
            # Confidence threshold analizi
            high_conf_signals = df[df['confidence'] >= 80]
            high_conf_success = high_conf_signals['is_successful'].mean() * 100 if len(high_conf_signals) > 0 else 0
            
            # Optimizasyon önerileri
            optimizations = {
                'current_performance': {
                    'success_rate': round(success_rate, 2),
                    'avg_profit': round(avg_profit, 2) if not pd.isna(avg_profit) else 0,
                    'avg_loss': round(avg_loss, 2) if not pd.isna(avg_loss) else 0,
                    'long_success_rate': round(long_performance, 2),
                    'short_success_rate': round(short_performance, 2),
                    'high_confidence_success': round(high_conf_success, 2)
                },
                'recommended_changes': []
            }
            
            # Parametre önerileri
            if success_rate < 60:
                optimizations['recommended_changes'].append("Minimum confidence threshold'ı 70'e yükselt")
                
            if long_performance > short_performance + 10:
                optimizations['recommended_changes'].append("Short sinyalleri için ek filtre ekle")
            elif short_performance > long_performance + 10:
                optimizations['recommended_changes'].append("Long sinyalleri için ek filtre ekle")
                
            if high_conf_success > success_rate + 15:
                optimizations['recommended_changes'].append("Confidence threshold'ı minimum 80 yap")
                
            # Stop loss nedenlerini analiz et
            failed_signals = [d for d in self.performance_data if not d['is_successful']]
            if failed_signals:
                sl_analysis = self.analyze_stop_loss_reasons(failed_signals)
                optimizations['stop_loss_analysis'] = sl_analysis
                
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Parametre optimizasyonu hatası: {e}")
            return {"error": str(e)}
            
    def train_prediction_model(self) -> bool:
        """Tahmin modelini eğit"""
        if len(self.performance_data) < 100:
            self.logger.warning("Model eğitimi için yeterli veri yok")
            return False
            
        try:
            # Eğitim verilerini hazırla
            features = []
            labels = []
            
            for data in self.performance_data:
                if 'analysis' in data:
                    feature_vector = self._extract_features(data['analysis'])
                    if feature_vector:
                        features.append(feature_vector)
                        labels.append(1 if data['is_successful'] else 0)
                        
            if len(features) < 50:
                return False
                
            X = np.array(features)
            y = np.array(labels)
            
            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Model eğitimi
            self.model.fit(X_train, y_train)
            
            # Model değerlendirmesi
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.logger.info(f"Model eğitimi tamamlandı - Accuracy: {accuracy:.2f}")
            self.is_trained = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model eğitimi hatası: {e}")
            return False
            
    def predict_signal_success(self, analysis: Dict) -> Optional[float]:
        """Sinyal başarı olasılığını tahmin et"""
        if not self.is_trained:
            return None
            
        try:
            feature_vector = self._extract_features(analysis)
            if not feature_vector:
                return None
                
            probability = self.model.predict_proba([feature_vector])[0][1]
            return probability
            
        except Exception as e:
            self.logger.error(f"Tahmin hatası: {e}")
            return None
            
    def _extract_features(self, analysis: Dict) -> Optional[List[float]]:
        """Analiz verisinden özellik vektörü çıkar"""
        try:
            indicators = analysis.get('indicators', {})
            trend = analysis.get('trend', {})
            
            features = [
                indicators.get('rsi', 50),
                indicators.get('macd', {}).get('histogram', 0),
                indicators.get('bollinger_bands', {}).get('position', 0.5),
                trend.get('adx', 0),
                indicators.get('volume', {}).get('cmf', 0),
                0,  # price_change_1h (placeholder)
                0   # volume_change_1h (placeholder)
            ]
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction hatası: {e}")
            return None
            
    def _save_performance_data(self):
        """Performans verilerini kaydet"""
        try:
            with open('data/performance_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            self.logger.error(f"Performans verisi kaydetme hatası: {e}")
            
    def load_performance_data(self):
        """Performans verilerini yükle"""
        try:
            with open('data/performance_data.json', 'r', encoding='utf-8') as f:
                self.performance_data = json.load(f)
                
            # Model eğitimini dene
            if len(self.performance_data) >= 100:
                self.train_prediction_model()
                
        except FileNotFoundError:
            self.logger.info("Performans verisi dosyası bulunamadı, yeni dosya oluşturulacak")
        except Exception as e:
            self.logger.error(f"Performans verisi yükleme hatası: {e}")
            
    def get_optimization_status(self) -> Dict:
        """Optimizasyon durumunu getir"""
        return {
            'total_signals_analyzed': len(self.performance_data),
            'model_trained': self.is_trained,
            'last_optimization': datetime.now().isoformat(),
            'performance_summary': self.optimize_parameters() if len(self.performance_data) >= 10 else None
        }