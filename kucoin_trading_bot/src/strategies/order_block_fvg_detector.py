"""
Order Block (OB) ve Fair Value Gap (FVG) Detection Engine
Smart Money Concepts için kritik seviyeler
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

class OrderBlockFVGDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_order_blocks(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Order Block tespiti - Güçlü hamle öncesi son karşı yönlü mum
        """
        try:
            order_blocks = {
                'bullish_ob': [],
                'bearish_ob': []
            }
            
            if len(df) < 10:
                return order_blocks
            
            # Son lookback mumları analiz et
            recent_data = df.tail(lookback)
            
            for i in range(5, len(recent_data) - 2):
                current_candle = recent_data.iloc[i]
                
                # Bullish Order Block tespiti
                if self._is_bullish_order_block(recent_data, i):
                    order_blocks['bullish_ob'].append({
                        'high': current_candle['high'],
                        'low': current_candle['low'],
                        'open': current_candle['open'],
                        'close': current_candle['close'],
                        'timestamp': recent_data.index[i],
                        'strength': self._calculate_ob_strength(recent_data, i, 'bullish'),
                        'tested': False,
                        'mitigation_count': 0
                    })
                
                # Bearish Order Block tespiti
                if self._is_bearish_order_block(recent_data, i):
                    order_blocks['bearish_ob'].append({
                        'high': current_candle['high'],
                        'low': current_candle['low'], 
                        'open': current_candle['open'],
                        'close': current_candle['close'],
                        'timestamp': recent_data.index[i],
                        'strength': self._calculate_ob_strength(recent_data, i, 'bearish'),
                        'tested': False,
                        'mitigation_count': 0
                    })
            
            # Güce göre sırala
            order_blocks['bullish_ob'].sort(key=lambda x: x['strength'], reverse=True)
            order_blocks['bearish_ob'].sort(key=lambda x: x['strength'], reverse=True)
            
            # En güçlü 5 tanesini al
            order_blocks['bullish_ob'] = order_blocks['bullish_ob'][:5]
            order_blocks['bearish_ob'] = order_blocks['bearish_ob'][:5]
            
            self.logger.debug(f"Order Blocks: {len(order_blocks['bullish_ob'])} bullish, {len(order_blocks['bearish_ob'])} bearish")
            
            return order_blocks
            
        except Exception as e:
            self.logger.error(f"Order Block tespiti hatası: {e}")
            return {'bullish_ob': [], 'bearish_ob': []}
    
    def _is_bullish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """
        Bullish Order Block kriterleri:
        1. Kırmızı mum (bearish)
        2. Sonrasında güçlü yükseliş (en az 3 mum)
        3. Bu mumun high'ını kıracak güçlü momentum
        """
        try:
            if index >= len(df) - 3:
                return False
                
            current = df.iloc[index]
            
            # 1. Mevcut mum bearish olmalı
            if not current['is_bearish']:
                return False
            
            # 2. Sonraki 3 mumda güçlü yükseliş
            bullish_count = 0
            total_move = 0
            
            for i in range(index + 1, min(index + 4, len(df))):
                next_candle = df.iloc[i]
                if next_candle['is_bullish']:
                    bullish_count += 1
                    total_move += next_candle['body_size']
            
            # En az 2/3 bullish mum ve current mumun high'ını kırmalı
            if bullish_count >= 2:
                highest_after = df.iloc[index+1:min(index+4, len(df))]['high'].max()
                if highest_after > current['high']:
                    return True
            
            return False
            
        except:
            return False
    
    def _is_bearish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """
        Bearish Order Block kriterleri:
        1. Yeşil mum (bullish)
        2. Sonrasında güçlü düşüş (en az 3 mum)
        3. Bu mumun low'unu kıracak güçlü momentum
        """
        try:
            if index >= len(df) - 3:
                return False
                
            current = df.iloc[index]
            
            # 1. Mevcut mum bullish olmalı
            if not current['is_bullish']:
                return False
            
            # 2. Sonraki 3 mumda güçlü düşüş
            bearish_count = 0
            total_move = 0
            
            for i in range(index + 1, min(index + 4, len(df))):
                next_candle = df.iloc[i]
                if next_candle['is_bearish']:
                    bearish_count += 1
                    total_move += next_candle['body_size']
            
            # En az 2/3 bearish mum ve current mumun low'unu kırmalı
            if bearish_count >= 2:
                lowest_after = df.iloc[index+1:min(index+4, len(df))]['low'].min()
                if lowest_after < current['low']:
                    return True
            
            return False
            
        except:
            return False
    
    def _calculate_ob_strength(self, df: pd.DataFrame, index: int, ob_type: str) -> float:
        """
        Order Block gücünü hesapla (0-100)
        """
        try:
            strength = 0
            current = df.iloc[index]
            
            # 1. Mum boyutu (25 puan)
            avg_body = df['body_size'].rolling(20).mean().iloc[index]
            if current['body_size'] > avg_body * 1.5:
                strength += 25
            elif current['body_size'] > avg_body:
                strength += 15
            
            # 2. Sonraki hareket gücü (35 puan)
            if ob_type == 'bullish':
                next_move = df.iloc[index+1:min(index+4, len(df))]['high'].max() - current['high']
            else:
                next_move = current['low'] - df.iloc[index+1:min(index+4, len(df))]['low'].min()
            
            avg_move = df['true_range'].rolling(20).mean().iloc[index]
            if next_move > avg_move * 2:
                strength += 35
            elif next_move > avg_move:
                strength += 20
            
            # 3. Hacim (20 puan)
            avg_volume = df['volume'].rolling(20).mean().iloc[index]
            if current['volume'] > avg_volume * 1.5:
                strength += 20
            elif current['volume'] > avg_volume:
                strength += 10
            
            # 4. Test edilmemiş olma (20 puan)
            strength += 20  # Başlangıçta test edilmemiş
            
            return min(strength, 100)
            
        except Exception as e:
            self.logger.error(f"OB strength hesaplama hatası: {e}")
            return 0
    
    def detect_fair_value_gaps(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Fair Value Gap (FVG) tespiti - 3 mum boşluk paterni
        """
        try:
            fvgs = {
                'bullish_fvg': [],
                'bearish_fvg': []
            }
            
            if len(df) < 3:
                return fvgs
            
            # Son lookback mumları analiz et
            recent_data = df.tail(lookback)
            
            for i in range(1, len(recent_data) - 1):
                candle1 = recent_data.iloc[i-1]  # İlk mum
                candle2 = recent_data.iloc[i]    # Orta mum (imbalance)
                candle3 = recent_data.iloc[i+1]  # Son mum
                
                # Bullish FVG tespiti
                bullish_fvg = self._detect_bullish_fvg(candle1, candle2, candle3)
                if bullish_fvg:
                    fvgs['bullish_fvg'].append({
                        'top': bullish_fvg['top'],
                        'bottom': bullish_fvg['bottom'],
                        'timestamp': recent_data.index[i],
                        'strength': self._calculate_fvg_strength(candle1, candle2, candle3, 'bullish'),
                        'filled': False,
                        'fill_percentage': 0
                    })
                
                # Bearish FVG tespiti
                bearish_fvg = self._detect_bearish_fvg(candle1, candle2, candle3)
                if bearish_fvg:
                    fvgs['bearish_fvg'].append({
                        'top': bearish_fvg['top'],
                        'bottom': bearish_fvg['bottom'],
                        'timestamp': recent_data.index[i],
                        'strength': self._calculate_fvg_strength(candle1, candle2, candle3, 'bearish'),
                        'filled': False,
                        'fill_percentage': 0
                    })
            
            # Güce göre sırala ve en güçlü 3 tanesini al
            fvgs['bullish_fvg'].sort(key=lambda x: x['strength'], reverse=True)
            fvgs['bearish_fvg'].sort(key=lambda x: x['strength'], reverse=True)
            
            fvgs['bullish_fvg'] = fvgs['bullish_fvg'][:3]
            fvgs['bearish_fvg'] = fvgs['bearish_fvg'][:3]
            
            self.logger.debug(f"FVGs: {len(fvgs['bullish_fvg'])} bullish, {len(fvgs['bearish_fvg'])} bearish")
            
            return fvgs
            
        except Exception as e:
            self.logger.error(f"FVG tespiti hatası: {e}")
            return {'bullish_fvg': [], 'bearish_fvg': []}
    
    def _detect_bullish_fvg(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series) -> Optional[Dict]:
        """
        Bullish FVG: 1. mumun high'ı < 3. mumun low'u
        Gap: candle1.high ile candle3.low arası
        """
        try:
            # Temel koşul: 1. mumun tepesi < 3. mumun dibi
            if candle1['high'] < candle3['low']:
                gap_size = candle3['low'] - candle1['high']
                
                # Minimum gap boyutu kontrolü (ATR'nin %10'u)
                if gap_size > 0:
                    return {
                        'top': candle3['low'],
                        'bottom': candle1['high'],
                        'size': gap_size
                    }
            
            return None
            
        except:
            return None
    
    def _detect_bearish_fvg(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series) -> Optional[Dict]:
        """
        Bearish FVG: 1. mumun low'u > 3. mumun high'ı
        Gap: candle3.high ile candle1.low arası
        """
        try:
            # Temel koşul: 1. mumun dibi > 3. mumun tepesi
            if candle1['low'] > candle3['high']:
                gap_size = candle1['low'] - candle3['high']
                
                # Minimum gap boyutu kontrolü
                if gap_size > 0:
                    return {
                        'top': candle1['low'],
                        'bottom': candle3['high'],
                        'size': gap_size
                    }
            
            return None
            
        except:
            return None
    
    def _calculate_fvg_strength(self, candle1: pd.Series, candle2: pd.Series, candle3: pd.Series, fvg_type: str) -> float:
        """
        FVG gücünü hesapla (0-100)
        """
        try:
            strength = 0
            
            # 1. Gap boyutu (40 puan)
            if fvg_type == 'bullish':
                gap_size = candle3['low'] - candle1['high']
            else:
                gap_size = candle1['low'] - candle3['high']
            
            avg_range = (candle1['true_range'] + candle2['true_range'] + candle3['true_range']) / 3
            
            if gap_size > avg_range * 0.5:
                strength += 40
            elif gap_size > avg_range * 0.3:
                strength += 25
            elif gap_size > avg_range * 0.1:
                strength += 15
            
            # 2. Orta mumun momentum gücü (30 puan)
            momentum_strength = candle2['body_size'] / avg_range
            if momentum_strength > 1.5:
                strength += 30
            elif momentum_strength > 1.0:
                strength += 20
            elif momentum_strength > 0.5:
                strength += 10
            
            # 3. Hacim konfirmasyonu (30 puan)
            avg_volume = (candle1['volume'] + candle2['volume'] + candle3['volume']) / 3
            if candle2['volume'] > avg_volume * 1.5:
                strength += 30
            elif candle2['volume'] > avg_volume:
                strength += 20
            
            return min(strength, 100)
            
        except Exception as e:
            self.logger.error(f"FVG strength hesaplama hatası: {e}")
            return 0
    
    def check_price_in_zones(self, current_price: float, order_blocks: Dict, fvgs: Dict) -> Dict:
        """
        Mevcut fiyatın OB/FVG bölgelerinde olup olmadığını kontrol et
        """
        try:
            result = {
                'in_bullish_ob': False,
                'in_bearish_ob': False,
                'in_bullish_fvg': False,
                'in_bearish_fvg': False,
                'active_zones': []
            }
            
            # Bullish Order Block kontrolü
            for ob in order_blocks.get('bullish_ob', []):
                if ob['low'] <= current_price <= ob['high']:
                    result['in_bullish_ob'] = True
                    result['active_zones'].append({
                        'type': 'bullish_ob',
                        'top': ob['high'],
                        'bottom': ob['low'],
                        'strength': ob['strength']
                    })
            
            # Bearish Order Block kontrolü
            for ob in order_blocks.get('bearish_ob', []):
                if ob['low'] <= current_price <= ob['high']:
                    result['in_bearish_ob'] = True
                    result['active_zones'].append({
                        'type': 'bearish_ob',
                        'top': ob['high'],
                        'bottom': ob['low'],
                        'strength': ob['strength']
                    })
            
            # Bullish FVG kontrolü
            for fvg in fvgs.get('bullish_fvg', []):
                if fvg['bottom'] <= current_price <= fvg['top'] and not fvg['filled']:
                    result['in_bullish_fvg'] = True
                    result['active_zones'].append({
                        'type': 'bullish_fvg',
                        'top': fvg['top'],
                        'bottom': fvg['bottom'],
                        'strength': fvg['strength']
                    })
            
            # Bearish FVG kontrolü
            for fvg in fvgs.get('bearish_fvg', []):
                if fvg['bottom'] <= current_price <= fvg['top'] and not fvg['filled']:
                    result['in_bearish_fvg'] = True
                    result['active_zones'].append({
                        'type': 'bearish_fvg',
                        'top': fvg['top'],
                        'bottom': fvg['bottom'],
                        'strength': fvg['strength']
                    })
            
            # En güçlü zona göre sırala
            result['active_zones'].sort(key=lambda x: x['strength'], reverse=True)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Zone kontrolü hatası: {e}")
            return {'in_bullish_ob': False, 'in_bearish_ob': False, 'in_bullish_fvg': False, 'in_bearish_fvg': False, 'active_zones': []}