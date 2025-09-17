"""
ADX + Directional Indicators (+DI/-DI) Filter System
Trend gücü ve yön onayı için filtre sistemi
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

class ADXDirectionalFilter:
    def __init__(self, period: int = 14):
        self.period = period
        self.logger = logging.getLogger(__name__)
        
    def calculate_adx_di(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        ADX, +DI, -DI hesaplama
        """
        try:
            # Kopyalama
            data = df.copy()
            
            # True Range hesaplama
            data['prev_close'] = data['close'].shift(1)
            data['tr1'] = data['high'] - data['low']
            data['tr2'] = abs(data['high'] - data['prev_close'])
            data['tr3'] = abs(data['low'] - data['prev_close'])
            data['true_range'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Directional Movement hesaplama
            data['high_diff'] = data['high'] - data['high'].shift(1)
            data['low_diff'] = data['low'].shift(1) - data['low']
            
            # +DM ve -DM
            data['plus_dm'] = np.where(
                (data['high_diff'] > data['low_diff']) & (data['high_diff'] > 0),
                data['high_diff'],
                0
            )
            
            data['minus_dm'] = np.where(
                (data['low_diff'] > data['high_diff']) & (data['low_diff'] > 0),
                data['low_diff'],
                0
            )
            
            # Smoothed TR, +DM, -DM (Wilder's smoothing)
            data['tr_smooth'] = self._wilder_smooth(data['true_range'], self.period)
            data['plus_dm_smooth'] = self._wilder_smooth(data['plus_dm'], self.period)
            data['minus_dm_smooth'] = self._wilder_smooth(data['minus_dm'], self.period)
            
            # +DI ve -DI hesaplama
            data['plus_di'] = 100 * (data['plus_dm_smooth'] / data['tr_smooth'])
            data['minus_di'] = 100 * (data['minus_dm_smooth'] / data['tr_smooth'])
            
            # DX hesaplama
            data['di_diff'] = abs(data['plus_di'] - data['minus_di'])
            data['di_sum'] = data['plus_di'] + data['minus_di']
            data['dx'] = 100 * (data['di_diff'] / data['di_sum'])
            
            # ADX hesaplama (DX'in Wilder smoothing'i)
            data['adx'] = self._wilder_smooth(data['dx'], self.period)
            
            # NaN değerleri temizle
            data['adx'] = data['adx'].fillna(0)
            data['plus_di'] = data['plus_di'].fillna(0)
            data['minus_di'] = data['minus_di'].fillna(0)
            
            return data
            
        except Exception as e:
            self.logger.error(f"ADX/DI hesaplama hatası: {e}")
            return df
    
    def _wilder_smooth(self, series: pd.Series, period: int) -> pd.Series:
        """
        Wilder's smoothing methodu
        """
        try:
            alpha = 1.0 / period
            return series.ewm(alpha=alpha, adjust=False).mean()
        except:
            return series.rolling(window=period).mean()
    
    def get_adx_signal(self, df: pd.DataFrame, min_adx: float = 25.0) -> Dict:
        """
        ADX ve DI sinyallerini analiz et
        """
        try:
            # ADX ve DI hesapla
            data = self.calculate_adx_di(df)
            
            if len(data) < self.period:
                return self._empty_signal()
            
            # Son değerleri al
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest
            
            result = {
                'adx': float(latest['adx']),
                'plus_di': float(latest['plus_di']),
                'minus_di': float(latest['minus_di']),
                'adx_strong': latest['adx'] >= min_adx,
                'trend_direction': self._get_trend_direction(latest),
                'trend_strength': self._get_trend_strength(latest['adx']),
                'directional_bias': self._get_directional_bias(latest),
                'signal_quality': self._calculate_signal_quality(latest, prev),
                'long_allowed': self._is_long_allowed(latest, min_adx),
                'short_allowed': self._is_short_allowed(latest, min_adx),
                'adx_rising': latest['adx'] > prev['adx'],
                'crossover_signal': self._detect_di_crossover(data)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"ADX signal analizi hatası: {e}")
            return self._empty_signal()
    
    def _get_trend_direction(self, latest: pd.Series) -> str:
        """
        Trend yönünü belirle
        """
        if latest['plus_di'] > latest['minus_di']:
            if latest['plus_di'] - latest['minus_di'] > 5:
                return "STRONG_BULLISH"
            else:
                return "BULLISH"
        elif latest['minus_di'] > latest['plus_di']:
            if latest['minus_di'] - latest['plus_di'] > 5:
                return "STRONG_BEARISH"
            else:
                return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _get_trend_strength(self, adx: float) -> str:
        """
        Trend gücünü kategorize et
        """
        if adx >= 50:
            return "VERY_STRONG"
        elif adx >= 35:
            return "STRONG"
        elif adx >= 25:
            return "MODERATE"
        elif adx >= 20:
            return "WEAK"
        else:
            return "NO_TREND"
    
    def _get_directional_bias(self, latest: pd.Series) -> str:
        """
        Yönlü bias belirle
        """
        di_diff = abs(latest['plus_di'] - latest['minus_di'])
        
        if di_diff < 3:
            return "NEUTRAL"
        elif latest['plus_di'] > latest['minus_di']:
            return "BULLISH"
        else:
            return "BEARISH"
    
    def _calculate_signal_quality(self, latest: pd.Series, prev: pd.Series) -> float:
        """
        Sinyal kalitesini hesapla (0-100)
        """
        try:
            quality = 0
            
            # 1. ADX gücü (40 puan)
            if latest['adx'] >= 50:
                quality += 40
            elif latest['adx'] >= 35:
                quality += 30
            elif latest['adx'] >= 25:
                quality += 20
            elif latest['adx'] >= 20:
                quality += 10
            
            # 2. DI ayrışması (30 puan)
            di_separation = abs(latest['plus_di'] - latest['minus_di'])
            if di_separation >= 15:
                quality += 30
            elif di_separation >= 10:
                quality += 20
            elif di_separation >= 5:
                quality += 15
            elif di_separation >= 3:
                quality += 10
            
            # 3. ADX trendi (20 puan)
            if latest['adx'] > prev['adx']:  # ADX yükseliyor
                adx_momentum = latest['adx'] - prev['adx']
                if adx_momentum >= 2:
                    quality += 20
                elif adx_momentum >= 1:
                    quality += 15
                elif adx_momentum >= 0.5:
                    quality += 10
            
            # 4. DI momentum (10 puan)
            if latest['plus_di'] > latest['minus_di']:  # Bullish
                if latest['plus_di'] > prev['plus_di'] and latest['minus_di'] < prev['minus_di']:
                    quality += 10
                elif latest['plus_di'] > prev['plus_di']:
                    quality += 5
            else:  # Bearish
                if latest['minus_di'] > prev['minus_di'] and latest['plus_di'] < prev['plus_di']:
                    quality += 10
                elif latest['minus_di'] > prev['minus_di']:
                    quality += 5
            
            return min(quality, 100)
            
        except:
            return 0
    
    def _is_long_allowed(self, latest: pd.Series, min_adx: float) -> bool:
        """
        LONG pozisyon için ADX/DI koşulları
        """
        return (
            latest['adx'] >= min_adx and
            latest['plus_di'] > latest['minus_di']
        )
    
    def _is_short_allowed(self, latest: pd.Series, min_adx: float) -> bool:
        """
        SHORT pozisyon için ADX/DI koşulları
        """
        return (
            latest['adx'] >= min_adx and
            latest['minus_di'] > latest['plus_di']
        )
    
    def _detect_di_crossover(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        +DI/-DI crossover tespiti
        """
        try:
            if len(data) < 3:
                return None
            
            current = data.iloc[-1]
            prev = data.iloc[-2]
            prev2 = data.iloc[-3]
            
            # Bullish crossover: +DI crosses above -DI
            if (prev['plus_di'] <= prev['minus_di'] and 
                current['plus_di'] > current['minus_di'] and
                current['adx'] >= 20):
                return {
                    'type': 'bullish_crossover',
                    'strength': current['adx'],
                    'plus_di': current['plus_di'],
                    'minus_di': current['minus_di']
                }
            
            # Bearish crossover: -DI crosses above +DI
            if (prev['minus_di'] <= prev['plus_di'] and 
                current['minus_di'] > current['plus_di'] and
                current['adx'] >= 20):
                return {
                    'type': 'bearish_crossover',
                    'strength': current['adx'],
                    'plus_di': current['plus_di'],
                    'minus_di': current['minus_di']
                }
            
            return None
            
        except:
            return None
    
    def _empty_signal(self) -> Dict:
        """
        Boş sinyal döndür
        """
        return {
            'adx': 0,
            'plus_di': 0,
            'minus_di': 0,
            'adx_strong': False,
            'trend_direction': "NEUTRAL",
            'trend_strength': "NO_TREND",
            'directional_bias': "NEUTRAL",
            'signal_quality': 0,
            'long_allowed': False,
            'short_allowed': False,
            'adx_rising': False,
            'crossover_signal': None
        }
    
    def validate_entry_conditions(self, adx_signal: Dict, signal_type: str) -> bool:
        """
        Giriş koşullarını doğrula
        """
        try:
            # Temel ADX kontrolü
            if not adx_signal['adx_strong']:
                return False
            
            # Sinyal kalitesi kontrolü
            if adx_signal['signal_quality'] < 50:
                return False
            
            # Yön kontrolü
            if signal_type.upper() == 'LONG':
                return adx_signal['long_allowed']
            elif signal_type.upper() == 'SHORT':
                return adx_signal['short_allowed']
            
            return False
            
        except Exception as e:
            self.logger.error(f"Entry conditions validation error: {e}")
            return False
    
    def get_filter_score(self, adx_signal: Dict, signal_type: str) -> float:
        """
        ADX filter skoru (0-100)
        """
        try:
            score = 0
            
            # ADX gücü (40 puan)
            if adx_signal['adx'] >= 50:
                score += 40
            elif adx_signal['adx'] >= 35:
                score += 30
            elif adx_signal['adx'] >= 25:
                score += 20
            
            # Yön uyumu (35 puan)
            if signal_type.upper() == 'LONG' and adx_signal['long_allowed']:
                di_diff = adx_signal['plus_di'] - adx_signal['minus_di']
                if di_diff >= 15:
                    score += 35
                elif di_diff >= 10:
                    score += 25
                elif di_diff >= 5:
                    score += 15
            elif signal_type.upper() == 'SHORT' and adx_signal['short_allowed']:
                di_diff = adx_signal['minus_di'] - adx_signal['plus_di']
                if di_diff >= 15:
                    score += 35
                elif di_diff >= 10:
                    score += 25
                elif di_diff >= 5:
                    score += 15
            
            # ADX momentum (15 puan)
            if adx_signal['adx_rising']:
                score += 15
            
            # Crossover bonusu (10 puan)
            if adx_signal['crossover_signal']:
                crossover_type = adx_signal['crossover_signal']['type']
                if ((signal_type.upper() == 'LONG' and 'bullish' in crossover_type) or
                    (signal_type.upper() == 'SHORT' and 'bearish' in crossover_type)):
                    score += 10
            
            return min(score, 100)
            
        except Exception as e:
            self.logger.error(f"Filter score calculation error: {e}")
            return 0