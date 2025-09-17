import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from kucoin_api import KuCoinAPI
from technical_analysis import TechnicalAnalyzer

class SignalValidator:
    def __init__(self, kucoin_api: KuCoinAPI):
        self.api = kucoin_api
        self.analyzer = TechnicalAnalyzer(kucoin_api)
        self.logger = logging.getLogger(__name__)
        
        self.validation_interval = 5  # dakika
        self.validation_candles = 2  # kaç mum takip edilecek
        self.pending_validations = {}
        
    async def validate_signal(self, signal_data: Dict) -> Dict:
        """Sinyali 5 dakikalık grafikte doğrula"""
        try:
            symbol = signal_data['symbol']
            signal_type = signal_data['signal_type']
            entry_price = signal_data['entry_price']
            validation_id = f"{symbol}_{int(datetime.now().timestamp())}"
            
            # Validation tracking başlat
            validation_data = {
                'validation_id': validation_id,
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': entry_price,
                'start_time': datetime.now(),
                'candles_checked': 0,
                'max_candles': self.validation_candles,
                'validation_scores': [],
                'final_decision': None,
                'confidence_boost': 0
            }
            
            self.pending_validations[validation_id] = validation_data
            
            # 2 mum süresince (10 dakika) takip et
            validation_result = await self._track_validation(validation_data)
            
            # Validation tamamlandığında listeden çıkar
            if validation_id in self.pending_validations:
                del self.pending_validations[validation_id]
                
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Sinyal doğrulama hatası: {e}")
            return {
                'is_validated': False,
                'confidence_boost': 0,
                'reason': f"Doğrulama hatası: {str(e)}"
            }
            
    async def _track_validation(self, validation_data: Dict) -> Dict:
        """Validation tracking süreci"""
        try:
            symbol = validation_data['symbol']
            signal_type = validation_data['signal_type']
            entry_price = validation_data['entry_price']
            max_candles = validation_data['max_candles']
            
            candles_checked = 0
            validation_scores = []
            
            while candles_checked < max_candles:
                # 5 dakika bekle (bir mum süresi)
                await asyncio.sleep(300)  # 300 saniye = 5 dakika
                
                # Güncel 5 dakikalık analiz yap
                analysis = self.analyzer.analyze_coin(symbol, '5min')
                
                if analysis:
                    # Validation skoru hesapla
                    score = self._calculate_validation_score(analysis, signal_type, entry_price)
                    validation_scores.append(score)
                    
                    self.logger.info(f"Validation {symbol} - Mum {candles_checked + 1}: Score {score}")
                else:
                    # Analiz yapılamazsa nötr skor
                    validation_scores.append(0.5)
                    
                candles_checked += 1
                validation_data['candles_checked'] = candles_checked
                validation_data['validation_scores'] = validation_scores
                
            # Final validation kararı
            final_result = self._make_final_validation_decision(validation_scores, signal_type)
            validation_data['final_decision'] = final_result
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Validation tracking hatası: {e}")
            return {
                'is_validated': False,
                'confidence_boost': 0,
                'reason': f"Tracking hatası: {str(e)}"
            }
            
    def _calculate_validation_score(self, analysis: Dict, signal_type: str, entry_price: float) -> float:
        """5 dakikalık analiz için validation skoru hesapla"""
        try:
            indicators = analysis.get('indicators', {})
            current_price = analysis.get('current_price', entry_price)
            
            # Fiyat hareketi skoru
            price_change = (current_price - entry_price) / entry_price
            if signal_type == "LONG":
                price_score = min(max(price_change * 100, -1), 1)  # -1 ile 1 arası
            else:  # SHORT
                price_score = min(max(-price_change * 100, -1), 1)
                
            # RSI skoru
            rsi = indicators.get('rsi', 50)
            if signal_type == "LONG":
                if rsi < 40:
                    rsi_score = 0.8
                elif rsi < 50:
                    rsi_score = 0.6
                elif rsi < 60:
                    rsi_score = 0.4
                else:
                    rsi_score = 0.2
            else:  # SHORT
                if rsi > 60:
                    rsi_score = 0.8
                elif rsi > 50:
                    rsi_score = 0.6
                elif rsi > 40:
                    rsi_score = 0.4
                else:
                    rsi_score = 0.2
                    
            # MACD skoru
            macd_data = indicators.get('macd', {})
            macd_histogram = macd_data.get('histogram', 0)
            
            if signal_type == "LONG":
                macd_score = 0.8 if macd_histogram > 0 else 0.2
            else:  # SHORT
                macd_score = 0.8 if macd_histogram < 0 else 0.2
                
            # Volume skoru
            volume_data = indicators.get('volume', {})
            cmf = volume_data.get('cmf', 0)
            
            if signal_type == "LONG":
                volume_score = 0.8 if cmf > 0 else 0.3
            else:  # SHORT
                volume_score = 0.8 if cmf < 0 else 0.3
                
            # Bollinger Bands skoru
            bb_data = indicators.get('bollinger_bands', {})
            bb_position = bb_data.get('position', 0.5)
            
            if signal_type == "LONG":
                if bb_position < 0.3:
                    bb_score = 0.8
                elif bb_position < 0.7:
                    bb_score = 0.6
                else:
                    bb_score = 0.3
            else:  # SHORT
                if bb_position > 0.7:
                    bb_score = 0.8
                elif bb_position > 0.3:
                    bb_score = 0.6
                else:
                    bb_score = 0.3
                    
            # Ağırlıklı ortalama skor
            total_score = (
                price_score * 0.3 +
                rsi_score * 0.25 +
                macd_score * 0.2 +
                volume_score * 0.15 +
                bb_score * 0.1
            )
            
            # 0-1 aralığına normalize et
            normalized_score = max(0, min(1, (total_score + 1) / 2))
            
            return normalized_score
            
        except Exception as e:
            self.logger.error(f"Validation skor hesaplama hatası: {e}")
            return 0.5  # Nötr skor
            
    def _make_final_validation_decision(self, scores: List[float], signal_type: str) -> Dict:
        """Final validation kararını ver"""
        try:
            if not scores:
                return {
                    'is_validated': False,
                    'confidence_boost': 0,
                    'reason': "Yeterli veri yok"
                }
                
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            # Trend kontrolü (skorlar artıyor mu?)
            trend_positive = len(scores) > 1 and scores[-1] > scores[0]
            
            # Karar kriterleri
            validation_threshold = 0.65
            consistency_threshold = 0.1  # Skorlar arasındaki fark
            
            is_consistent = (max_score - min_score) <= consistency_threshold
            is_strong = avg_score >= validation_threshold
            
            # Validation kararı
            if is_strong and is_consistent:
                confidence_boost = 20
                decision = True
                reason = f"Güçlü doğrulama (Ort: {avg_score:.2f})"
            elif is_strong:
                confidence_boost = 15
                decision = True
                reason = f"İyi doğrulama (Ort: {avg_score:.2f})"
            elif trend_positive and avg_score > 0.55:
                confidence_boost = 10
                decision = True
                reason = f"Pozitif trend (Ort: {avg_score:.2f})"
            else:
                confidence_boost = 0
                decision = False
                reason = f"Zayıf doğrulama (Ort: {avg_score:.2f})"
                
            # Trend bonusu
            if trend_positive and decision:
                confidence_boost += 5
                
            result = {
                'is_validated': decision,
                'confidence_boost': confidence_boost,
                'reason': reason,
                'validation_details': {
                    'average_score': round(avg_score, 3),
                    'min_score': round(min_score, 3),
                    'max_score': round(max_score, 3),
                    'consistency': round(max_score - min_score, 3),
                    'trend_positive': trend_positive,
                    'individual_scores': [round(s, 3) for s in scores]
                }
            }
            
            self.logger.info(f"Validation sonucu: {decision} - {reason}")
            return result
            
        except Exception as e:
            self.logger.error(f"Final validation kararı hatası: {e}")
            return {
                'is_validated': False,
                'confidence_boost': 0,
                'reason': f"Karar hatası: {str(e)}"
            }
            
    def get_pending_validations_status(self) -> Dict:
        """Bekleyen validation'ların durumu"""
        return {
            'total_pending': len(self.pending_validations),
            'validations': list(self.pending_validations.values())
        }
        
    async def quick_validate_signal(self, signal_data: Dict) -> Dict:
        """Hızlı sinyal doğrulama (tek mum)"""
        try:
            symbol = signal_data['symbol']
            signal_type = signal_data['signal_type']
            entry_price = signal_data['entry_price']
            
            # Mevcut 5 dakikalık analizi al
            analysis = self.analyzer.analyze_coin(symbol, '5min')
            
            if not analysis:
                return {
                    'is_validated': False,
                    'confidence_boost': 0,
                    'reason': "Analiz verisi alınamadı"
                }
                
            # Tek mum skoru hesapla
            score = self._calculate_validation_score(analysis, signal_type, entry_price)
            
            # Hızlı karar ver
            if score >= 0.7:
                confidence_boost = 15
                decision = True
                reason = f"Güçlü anlık doğrulama (Skor: {score:.2f})"
            elif score >= 0.6:
                confidence_boost = 10
                decision = True
                reason = f"İyi anlık doğrulama (Skor: {score:.2f})"
            elif score >= 0.5:
                confidence_boost = 5
                decision = True
                reason = f"Orta anlık doğrulama (Skor: {score:.2f})"
            else:
                confidence_boost = 0
                decision = False
                reason = f"Zayıf anlık doğrulama (Skor: {score:.2f})"
                
            return {
                'is_validated': decision,
                'confidence_boost': confidence_boost,
                'reason': reason,
                'quick_validation_score': round(score, 3)
            }
            
        except Exception as e:
            self.logger.error(f"Hızlı validation hatası: {e}")
            return {
                'is_validated': False,
                'confidence_boost': 0,
                'reason': f"Hızlı doğrulama hatası: {str(e)}"
            }
            
    async def validate_multiple_timeframes(self, signal_data: Dict) -> Dict:
        """Çoklu zaman dilimi doğrulama"""
        try:
            symbol = signal_data['symbol']
            signal_type = signal_data['signal_type']
            entry_price = signal_data['entry_price']
            
            timeframes = ['5min', '15min', '1hour']
            validations = {}
            total_boost = 0
            
            for tf in timeframes:
                try:
                    analysis = self.analyzer.analyze_coin(symbol, tf)
                    if analysis:
                        score = self._calculate_validation_score(analysis, signal_type, entry_price)
                        validations[tf] = {
                            'score': round(score, 3),
                            'is_positive': score >= 0.6
                        }
                        
                        # Zaman dilimine göre ağırlık
                        if tf == '5min':
                            weight = 0.5
                        elif tf == '15min':
                            weight = 0.3
                        else:  # 1hour
                            weight = 0.2
                            
                        if score >= 0.6:
                            total_boost += score * 20 * weight
                            
                except Exception as e:
                    self.logger.warning(f"Timeframe {tf} analizi hatası: {e}")
                    validations[tf] = {'score': 0.5, 'is_positive': False}
                    
            # Genel değerlendirme
            positive_count = sum(1 for v in validations.values() if v['is_positive'])
            avg_score = sum(v['score'] for v in validations.values()) / len(validations)
            
            is_validated = positive_count >= 2 or avg_score >= 0.65
            confidence_boost = min(total_boost, 25)  # Max 25 boost
            
            return {
                'is_validated': is_validated,
                'confidence_boost': round(confidence_boost),
                'reason': f"Multi-TF: {positive_count}/{len(timeframes)} pozitif",
                'timeframe_validations': validations,
                'average_score': round(avg_score, 3)
            }
            
        except Exception as e:
            self.logger.error(f"Multi-timeframe validation hatası: {e}")
            return {
                'is_validated': False,
                'confidence_boost': 0,
                'reason': f"Multi-TF doğrulama hatası: {str(e)}"
            }