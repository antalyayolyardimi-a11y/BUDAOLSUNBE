"""
M5 Confirmation System - 2 Mum Onay Sistemi
"""

import pandas as pd
import numpy as np
import logging
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta

class M5ConfirmationSystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def confirm_signal_on_m5(self, symbol: str, signal: Dict, kucoin_api) -> Dict:
        """M5'te 2 mum onay sistemi"""
        try:
            confirmation_result = {
                'confirmed': False,
                'reason': '',
                'candle_analysis': [],
                'final_entry_price': signal.get('entry_price', 0),
                'confirmation_strength': 0
            }
            
            # M5 data al - son 1 saat (12 mum)
            current_time = int(time.time())
            start_time = current_time - (60 * 60)  # 1 saat öncesi
            
            m5_klines = kucoin_api.get_klines(symbol, "5min", start_time=start_time, end_time=current_time)
            if m5_klines is None or len(m5_klines) < 3:
                confirmation_result['reason'] = "M5 data yetersiz"
                return confirmation_result
            
            # Klines'ı DataFrame'e çevir
            df_columns = ['timestamp', 'open', 'close', 'high', 'low', 'volume', 'turnover']
            m5_data = pd.DataFrame(m5_klines, columns=df_columns)
            
            # Veri tiplerini düzelt
            for col in ['open', 'close', 'high', 'low', 'volume', 'turnover']:
                m5_data[col] = pd.to_numeric(m5_data[col], errors='coerce')
            
            # Signal type'a göre onay ara
            signal_type = signal.get('signal', '').upper()
            
            if signal_type == "LONG":
                return await self._confirm_long_signal(m5_data, signal, confirmation_result)
            elif signal_type == "SHORT":
                return await self._confirm_short_signal(m5_data, signal, confirmation_result)
            else:
                confirmation_result['reason'] = "Geçersiz signal type"
                return confirmation_result
                
        except Exception as e:
            self.logger.error(f"M5 onay sistemi hatası: {e}")
            return {
                'confirmed': False,
                'reason': f"Onay sistemi hatası: {e}",
                'candle_analysis': [],
                'final_entry_price': signal.get('entry_price', 0),
                'confirmation_strength': 0
            }
    
    async def _confirm_long_signal(self, m5_data: pd.DataFrame, signal: Dict, result: Dict) -> Dict:
        """LONG sinyali M5 onayı"""
        try:
            # Son 2 mumu analiz et
            candle_1 = m5_data.iloc[-2]  # Bir önceki mum
            candle_2 = m5_data.iloc[-1]  # Son mum
            
            confirmation_points = 0
            max_points = 10
            
            # OB/FVG bölgesine dokunma kontrolü
            ob_fvg_zone = self._get_ob_fvg_zone(signal)
            
            # 1. MUM ANALİZİ (Candle 1)
            candle_1_analysis = self._analyze_candle_for_long(candle_1, ob_fvg_zone, "Mum 1")
            result['candle_analysis'].append(candle_1_analysis)
            confirmation_points += candle_1_analysis['points']
            
            # 2. MUM ANALİZİ (Candle 2) 
            candle_2_analysis = self._analyze_candle_for_long(candle_2, ob_fvg_zone, "Mum 2")
            result['candle_analysis'].append(candle_2_analysis)
            confirmation_points += candle_2_analysis['points']
            
            # GENEL DEĞERLENDİRME
            result['confirmation_strength'] = (confirmation_points / max_points) * 100
            
            # Onay kriterleri
            if confirmation_points >= 6:  # %60 başarı
                result['confirmed'] = True
                result['reason'] = f"M5 onayı başarılı - {confirmation_points}/{max_points} puan"
                # En son mumun close'unu entry price olarak kullan
                result['final_entry_price'] = float(candle_2['close'])
            else:
                result['confirmed'] = False
                result['reason'] = f"M5 onayı yetersiz - {confirmation_points}/{max_points} puan"
            
            return result
            
        except Exception as e:
            self.logger.error(f"LONG onay analizi hatası: {e}")
            result['confirmed'] = False
            result['reason'] = f"LONG onay hatası: {e}"
            return result
    
    async def _confirm_short_signal(self, m5_data: pd.DataFrame, signal: Dict, result: Dict) -> Dict:
        """SHORT sinyali M5 onayı"""
        try:
            # Son 2 mumu analiz et
            candle_1 = m5_data.iloc[-2]  # Bir önceki mum
            candle_2 = m5_data.iloc[-1]  # Son mum
            
            confirmation_points = 0
            max_points = 10
            
            # OB/FVG bölgesine dokunma kontrolü
            ob_fvg_zone = self._get_ob_fvg_zone(signal)
            
            # 1. MUM ANALİZİ (Candle 1)
            candle_1_analysis = self._analyze_candle_for_short(candle_1, ob_fvg_zone, "Mum 1")
            result['candle_analysis'].append(candle_1_analysis)
            confirmation_points += candle_1_analysis['points']
            
            # 2. MUM ANALİZİ (Candle 2)
            candle_2_analysis = self._analyze_candle_for_short(candle_2, ob_fvg_zone, "Mum 2")
            result['candle_analysis'].append(candle_2_analysis)
            confirmation_points += candle_2_analysis['points']
            
            # GENEL DEĞERLENDİRME
            result['confirmation_strength'] = (confirmation_points / max_points) * 100
            
            # Onay kriterleri
            if confirmation_points >= 6:  # %60 başarı
                result['confirmed'] = True
                result['reason'] = f"M5 onayı başarılı - {confirmation_points}/{max_points} puan"
                # En son mumun close'unu entry price olarak kullan
                result['final_entry_price'] = float(candle_2['close'])
            else:
                result['confirmed'] = False
                result['reason'] = f"M5 onayı yetersiz - {confirmation_points}/{max_points} puan"
            
            return result
            
        except Exception as e:
            self.logger.error(f"SHORT onay analizi hatası: {e}")
            result['confirmed'] = False
            result['reason'] = f"SHORT onay hatası: {e}"
            return result
    
    def _get_ob_fvg_zone(self, signal: Dict) -> Dict:
        """OB/FVG bölge bilgilerini al"""
        try:
            # Signal içinden zone bilgilerini çıkar
            zone_info = signal.get('zone_info', {})
            return {
                'top': zone_info.get('top', signal.get('entry_price', 0) * 1.002),
                'bottom': zone_info.get('bottom', signal.get('entry_price', 0) * 0.998),
                'type': zone_info.get('type', 'unknown')
            }
        except:
            entry_price = signal.get('entry_price', 0)
            return {
                'top': entry_price * 1.002,
                'bottom': entry_price * 0.998,
                'type': 'estimated'
            }
    
    def _analyze_candle_for_long(self, candle: pd.Series, ob_fvg_zone: Dict, candle_name: str) -> Dict:
        """LONG için mum analizi"""
        try:
            analysis = {
                'candle': candle_name,
                'points': 0,
                'details': [],
                'candle_type': 'neutral'
            }
            
            high = float(candle['high'])
            low = float(candle['low'])
            open_price = float(candle['open'])
            close = float(candle['close'])
            
            body_size = abs(close - open_price)
            candle_range = high - low
            upper_wick = high - max(open_price, close)
            lower_wick = min(open_price, close) - low
            
            # 1. OB/FVG bölgesine dokunma (3 puan)
            if low <= ob_fvg_zone['bottom'] <= high:
                analysis['points'] += 3
                analysis['details'].append("✅ OB/FVG bölgesine dokundu")
                analysis['candle_type'] = 'zone_touch'
            
            # 2. Rejection (Fitil tepkisi) (2 puan)
            if lower_wick > body_size * 1.5:  # Alt fitil gövdeden büyük
                analysis['points'] += 2
                analysis['details'].append("✅ Güçlü alt fitil rejection")
            elif lower_wick > body_size:
                analysis['points'] += 1
                analysis['details'].append("🟡 Orta seviye rejection")
                
            # 3. Bullish mum (2 puan)
            if close > open_price:
                if body_size > candle_range * 0.6:  # Güçlü yeşil mum
                    analysis['points'] += 2
                    analysis['details'].append("✅ Güçlü bullish mum")
                    analysis['candle_type'] = 'strong_bullish'
                else:
                    analysis['points'] += 1
                    analysis['details'].append("🟡 Zayıf bullish mum")
            
            # 4. Hacim kontrolü (1 puan) - varsa
            if hasattr(candle, 'volume') and candle['volume'] > 0:
                analysis['points'] += 1
                analysis['details'].append("✅ Hacim mevcut")
            
            # 5. Kapanış bölgenin üstünde (2 puan)
            if close > ob_fvg_zone['top']:
                analysis['points'] += 2
                analysis['details'].append("✅ Bölgenin üstünde kapanış")
            elif close > ob_fvg_zone['bottom']:
                analysis['points'] += 1
                analysis['details'].append("🟡 Bölge içinde kapanış")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LONG mum analizi hatası: {e}")
            return {
                'candle': candle_name,
                'points': 0,
                'details': [f"❌ Analiz hatası: {e}"],
                'candle_type': 'error'
            }
    
    def _analyze_candle_for_short(self, candle: pd.Series, ob_fvg_zone: Dict, candle_name: str) -> Dict:
        """SHORT için mum analizi"""
        try:
            analysis = {
                'candle': candle_name,
                'points': 0,
                'details': [],
                'candle_type': 'neutral'
            }
            
            high = float(candle['high'])
            low = float(candle['low'])
            open_price = float(candle['open'])
            close = float(candle['close'])
            
            body_size = abs(close - open_price)
            candle_range = high - low
            upper_wick = high - max(open_price, close)
            lower_wick = min(open_price, close) - low
            
            # 1. OB/FVG bölgesine dokunma (3 puan)
            if low <= ob_fvg_zone['top'] <= high:
                analysis['points'] += 3
                analysis['details'].append("✅ OB/FVG bölgesine dokundu")
                analysis['candle_type'] = 'zone_touch'
            
            # 2. Rejection (Fitil tepkisi) (2 puan)
            if upper_wick > body_size * 1.5:  # Üst fitil gövdeden büyük
                analysis['points'] += 2
                analysis['details'].append("✅ Güçlü üst fitil rejection")
            elif upper_wick > body_size:
                analysis['points'] += 1
                analysis['details'].append("🟡 Orta seviye rejection")
                
            # 3. Bearish mum (2 puan)
            if close < open_price:
                if body_size > candle_range * 0.6:  # Güçlü kırmızı mum
                    analysis['points'] += 2
                    analysis['details'].append("✅ Güçlü bearish mum")
                    analysis['candle_type'] = 'strong_bearish'
                else:
                    analysis['points'] += 1
                    analysis['details'].append("🟡 Zayıf bearish mum")
            
            # 4. Hacim kontrolü (1 puan)
            if hasattr(candle, 'volume') and candle['volume'] > 0:
                analysis['points'] += 1
                analysis['details'].append("✅ Hacim mevcut")
            
            # 5. Kapanış bölgenin altında (2 puan)
            if close < ob_fvg_zone['bottom']:
                analysis['points'] += 2
                analysis['details'].append("✅ Bölgenin altında kapanış")
            elif close < ob_fvg_zone['top']:
                analysis['points'] += 1
                analysis['details'].append("🟡 Bölge içinde kapanış")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"SHORT mum analizi hatası: {e}")
            return {
                'candle': candle_name,
                'points': 0,
                'details': [f"❌ Analiz hatası: {e}"],
                'candle_type': 'error'
            }