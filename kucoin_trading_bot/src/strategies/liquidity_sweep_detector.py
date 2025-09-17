"""
Liquidity Sweep & Market Structure Analysis
CHoCH (Change of Character) ve BOS (Break of Structure) tespiti
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

class LiquiditySweepDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_market_structure(self, df: pd.DataFrame) -> Dict:
        """
        Market yapısını analiz et: CHoCH, BOS, Liquidity Sweeps
        """
        try:
            result = {
                'swing_points': self._find_swing_points(df),
                'liquidity_sweeps': [],
                'choch_signals': [],
                'bos_signals': [],
                'market_structure': 'NEUTRAL'
            }
            
            swing_points = result['swing_points']
            
            if len(swing_points['highs']) >= 2 and len(swing_points['lows']) >= 2:
                # Liquidity sweeps tespit et
                result['liquidity_sweeps'] = self._detect_liquidity_sweeps(df, swing_points)
                
                # CHoCH tespiti
                result['choch_signals'] = self._detect_choch(df, swing_points)
                
                # BOS tespiti  
                result['bos_signals'] = self._detect_bos(df, swing_points)
                
                # Genel market yapısını belirle
                result['market_structure'] = self._determine_market_structure(swing_points)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Market structure analysis error: {e}")
            return {
                'swing_points': {'highs': [], 'lows': []},
                'liquidity_sweeps': [],
                'choch_signals': [],
                'bos_signals': [],
                'market_structure': 'NEUTRAL'
            }
    
    def _find_swing_points(self, df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Swing high ve swing low noktalarını bul
        """
        try:
            highs = []
            lows = []
            
            for i in range(lookback, len(df) - lookback):
                current_high = df.iloc[i]['high']
                current_low = df.iloc[i]['low']
                
                # Swing High kontrolü
                is_swing_high = True
                for j in range(i - lookback, i + lookback + 1):
                    if j != i and df.iloc[j]['high'] >= current_high:
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    highs.append({
                        'price': current_high,
                        'index': i,
                        'timestamp': df.index[i],
                        'tested': False,
                        'swept': False
                    })
                
                # Swing Low kontrolü
                is_swing_low = True
                for j in range(i - lookback, i + lookback + 1):
                    if j != i and df.iloc[j]['low'] <= current_low:
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    lows.append({
                        'price': current_low,
                        'index': i,
                        'timestamp': df.index[i],
                        'tested': False,
                        'swept': False
                    })
            
            # Son 10 swing point al
            highs = sorted(highs, key=lambda x: x['timestamp'])[-10:]
            lows = sorted(lows, key=lambda x: x['timestamp'])[-10:]
            
            return {'highs': highs, 'lows': lows}
            
        except Exception as e:
            self.logger.error(f"Swing points detection error: {e}")
            return {'highs': [], 'lows': []}
    
    def _detect_liquidity_sweeps(self, df: pd.DataFrame, swing_points: Dict) -> List[Dict]:
        """
        Liquidity sweep tespiti - Fitil ile dip/tepe üstü sweep
        """
        try:
            sweeps = []
            
            # Son 20 mumda sweep ara
            recent_data = df.tail(20)
            
            for i, candle in recent_data.iterrows():
                timestamp = i
                
                # High sweep kontrolü (dip üstü sweep)
                for swing_high in swing_points['highs']:
                    if not swing_high['swept'] and timestamp > swing_high['timestamp']:
                        # Fitil swing high'ı geçmiş mi?
                        if candle['high'] > swing_high['price']:
                            # Ama kapanış swing high altında mı? (False breakout)
                            if candle['close'] < swing_high['price']:
                                sweeps.append({
                                    'type': 'high_sweep',
                                    'timestamp': timestamp,
                                    'sweep_price': candle['high'],
                                    'liquidity_level': swing_high['price'],
                                    'candle_close': candle['close'],
                                    'strength': self._calculate_sweep_strength(candle, swing_high, 'high'),
                                    'swing_point': swing_high
                                })
                                swing_high['swept'] = True
                
                # Low sweep kontrolü (tepe altı sweep)
                for swing_low in swing_points['lows']:
                    if not swing_low['swept'] and timestamp > swing_low['timestamp']:
                        # Fitil swing low'u geçmiş mi?
                        if candle['low'] < swing_low['price']:
                            # Ama kapanış swing low üstünde mi? (False breakout)
                            if candle['close'] > swing_low['price']:
                                sweeps.append({
                                    'type': 'low_sweep',
                                    'timestamp': timestamp,
                                    'sweep_price': candle['low'],
                                    'liquidity_level': swing_low['price'],
                                    'candle_close': candle['close'],
                                    'strength': self._calculate_sweep_strength(candle, swing_low, 'low'),
                                    'swing_point': swing_low
                                })
                                swing_low['swept'] = True
            
            # Güce göre sırala
            sweeps.sort(key=lambda x: x['strength'], reverse=True)
            
            return sweeps
            
        except Exception as e:
            self.logger.error(f"Liquidity sweep detection error: {e}")
            return []
    
    def _calculate_sweep_strength(self, candle: pd.Series, swing_point: Dict, sweep_type: str) -> float:
        """
        Sweep gücünü hesapla (0-100)
        """
        try:
            strength = 0
            
            # 1. Penetration depth (40 puan)
            if sweep_type == 'high':
                penetration = candle['high'] - swing_point['price']
                wick_size = candle['high'] - max(candle['open'], candle['close'])
            else:
                penetration = swing_point['price'] - candle['low']
                wick_size = min(candle['open'], candle['close']) - candle['low']
            
            body_size = abs(candle['close'] - candle['open'])
            
            if penetration > body_size * 0.5:
                strength += 40
            elif penetration > body_size * 0.3:
                strength += 30
            elif penetration > body_size * 0.1:
                strength += 20
            
            # 2. Wick to body ratio (30 puan)
            if body_size > 0:
                wick_ratio = wick_size / body_size
                if wick_ratio > 2.0:
                    strength += 30
                elif wick_ratio > 1.5:
                    strength += 20
                elif wick_ratio > 1.0:
                    strength += 15
            
            # 3. Immediate rejection (30 puan)
            if sweep_type == 'high':
                rejection = (candle['high'] - candle['close']) / (candle['high'] - candle['low'])
            else:
                rejection = (candle['close'] - candle['low']) / (candle['high'] - candle['low'])
            
            if rejection > 0.7:
                strength += 30
            elif rejection > 0.5:
                strength += 20
            elif rejection > 0.3:
                strength += 10
            
            return min(strength, 100)
            
        except:
            return 0
    
    def _detect_choch(self, df: pd.DataFrame, swing_points: Dict) -> List[Dict]:
        """
        Change of Character (CHoCH) tespiti
        İlk karşı yönlü swing point kırılması
        """
        try:
            choch_signals = []
            
            # Son 10 mumda CHoCH ara
            recent_data = df.tail(10)
            
            for i, candle in recent_data.iterrows():
                timestamp = i
                
                # Bullish CHoCH: Son LH (Lower High) yukarı kırılırsa
                recent_lh = self._get_recent_lower_high(swing_points['highs'])
                if recent_lh and candle['close'] > recent_lh['price']:
                    # Bu LH daha önce kırılmış mı kontrol et
                    if not recent_lh.get('broken', False):
                        choch_signals.append({
                            'type': 'bullish_choch',
                            'timestamp': timestamp,
                            'break_price': candle['close'],
                            'broken_level': recent_lh['price'],
                            'strength': self._calculate_choch_strength(candle, recent_lh, 'bullish'),
                            'swing_point': recent_lh
                        })
                        recent_lh['broken'] = True
                
                # Bearish CHoCH: Son HL (Higher Low) aşağı kırılırsa
                recent_hl = self._get_recent_higher_low(swing_points['lows'])
                if recent_hl and candle['close'] < recent_hl['price']:
                    # Bu HL daha önce kırılmış mı kontrol et
                    if not recent_hl.get('broken', False):
                        choch_signals.append({
                            'type': 'bearish_choch',
                            'timestamp': timestamp,
                            'break_price': candle['close'],
                            'broken_level': recent_hl['price'],
                            'strength': self._calculate_choch_strength(candle, recent_hl, 'bearish'),
                            'swing_point': recent_hl
                        })
                        recent_hl['broken'] = True
            
            return choch_signals
            
        except Exception as e:
            self.logger.error(f"CHoCH detection error: {e}")
            return []
    
    def _detect_bos(self, df: pd.DataFrame, swing_points: Dict) -> List[Dict]:
        """
        Break of Structure (BOS) tespiti
        Trend yönündeki swing point kırılması
        """
        try:
            bos_signals = []
            
            # Son 10 mumda BOS ara
            recent_data = df.tail(10)
            
            for i, candle in recent_data.iterrows():
                timestamp = i
                
                # Bullish BOS: Son HH (Higher High) yukarı kırılırsa
                recent_hh = self._get_recent_higher_high(swing_points['highs'])
                if recent_hh and candle['close'] > recent_hh['price']:
                    if not recent_hh.get('broken', False):
                        bos_signals.append({
                            'type': 'bullish_bos',
                            'timestamp': timestamp,
                            'break_price': candle['close'],
                            'broken_level': recent_hh['price'],
                            'strength': self._calculate_bos_strength(candle, recent_hh, 'bullish'),
                            'swing_point': recent_hh
                        })
                        recent_hh['broken'] = True
                
                # Bearish BOS: Son LL (Lower Low) aşağı kırılırsa
                recent_ll = self._get_recent_lower_low(swing_points['lows'])
                if recent_ll and candle['close'] < recent_ll['price']:
                    if not recent_ll.get('broken', False):
                        bos_signals.append({
                            'type': 'bearish_bos',
                            'timestamp': timestamp,
                            'break_price': candle['close'],
                            'broken_level': recent_ll['price'],
                            'strength': self._calculate_bos_strength(candle, recent_ll, 'bearish'),
                            'swing_point': recent_ll
                        })
                        recent_ll['broken'] = True
            
            return bos_signals
            
        except Exception as e:
            self.logger.error(f"BOS detection error: {e}")
            return []
    
    def _get_recent_lower_high(self, highs: List[Dict]) -> Optional[Dict]:
        """
        En son Lower High'ı bul
        """
        if len(highs) < 2:
            return None
        
        sorted_highs = sorted(highs, key=lambda x: x['timestamp'])
        
        for i in range(len(sorted_highs) - 1, 0, -1):
            current = sorted_highs[i]
            previous = sorted_highs[i-1]
            
            if current['price'] < previous['price']:  # Lower High
                return current
        
        return None
    
    def _get_recent_higher_low(self, lows: List[Dict]) -> Optional[Dict]:
        """
        En son Higher Low'u bul
        """
        if len(lows) < 2:
            return None
        
        sorted_lows = sorted(lows, key=lambda x: x['timestamp'])
        
        for i in range(len(sorted_lows) - 1, 0, -1):
            current = sorted_lows[i]
            previous = sorted_lows[i-1]
            
            if current['price'] > previous['price']:  # Higher Low
                return current
        
        return None
    
    def _get_recent_higher_high(self, highs: List[Dict]) -> Optional[Dict]:
        """
        En son Higher High'ı bul
        """
        if len(highs) < 2:
            return None
        
        sorted_highs = sorted(highs, key=lambda x: x['timestamp'])
        
        for i in range(len(sorted_highs) - 1, 0, -1):
            current = sorted_highs[i]
            previous = sorted_highs[i-1]
            
            if current['price'] > previous['price']:  # Higher High
                return current
        
        return None
    
    def _get_recent_lower_low(self, lows: List[Dict]) -> Optional[Dict]:
        """
        En son Lower Low'u bul
        """
        if len(lows) < 2:
            return None
        
        sorted_lows = sorted(lows, key=lambda x: x['timestamp'])
        
        for i in range(len(sorted_lows) - 1, 0, -1):
            current = sorted_lows[i]
            previous = sorted_lows[i-1]
            
            if current['price'] < previous['price']:  # Lower Low
                return current
        
        return None
    
    def _calculate_choch_strength(self, candle: pd.Series, swing_point: Dict, choch_type: str) -> float:
        """
        CHoCH gücünü hesapla
        """
        try:
            strength = 0
            
            # 1. Penetration gücü (50 puan)
            if choch_type == 'bullish':
                penetration = candle['close'] - swing_point['price']
            else:
                penetration = swing_point['price'] - candle['close']
            
            body_size = abs(candle['close'] - candle['open'])
            
            if penetration > body_size:
                strength += 50
            elif penetration > body_size * 0.5:
                strength += 35
            elif penetration > body_size * 0.2:
                strength += 25
            
            # 2. Mum gücü (30 puan)
            if body_size > 0:
                total_range = candle['high'] - candle['low']
                body_ratio = body_size / total_range if total_range > 0 else 0
                
                if body_ratio > 0.7:
                    strength += 30
                elif body_ratio > 0.5:
                    strength += 20
                elif body_ratio > 0.3:
                    strength += 10
            
            # 3. Volume confirmation (20 puan)
            # Bu kısım volume verisi varsa eklenebilir
            strength += 10  # Placeholder
            
            return min(strength, 100)
            
        except:
            return 0
    
    def _calculate_bos_strength(self, candle: pd.Series, swing_point: Dict, bos_type: str) -> float:
        """
        BOS gücünü hesapla
        """
        # CHoCH ile aynı logic, ama trend yönünde olduğu için daha güçlü
        base_strength = self._calculate_choch_strength(candle, swing_point, bos_type)
        return min(base_strength * 1.2, 100)  # %20 bonus
    
    def _determine_market_structure(self, swing_points: Dict) -> str:
        """
        Genel market yapısını belirle
        """
        try:
            highs = swing_points['highs']
            lows = swing_points['lows']
            
            if len(highs) < 2 or len(lows) < 2:
                return 'NEUTRAL'
            
            # Son 2 swing high/low'u karşılaştır
            recent_highs = sorted(highs, key=lambda x: x['timestamp'])[-2:]
            recent_lows = sorted(lows, key=lambda x: x['timestamp'])[-2:]
            
            # Higher Highs ve Higher Lows
            hh = recent_highs[1]['price'] > recent_highs[0]['price']
            hl = recent_lows[1]['price'] > recent_lows[0]['price']
            
            # Lower Lows ve Lower Highs
            ll = recent_lows[1]['price'] < recent_lows[0]['price']
            lh = recent_highs[1]['price'] < recent_highs[0]['price']
            
            if hh and hl:
                return 'BULLISH'
            elif ll and lh:
                return 'BEARISH'
            else:
                return 'RANGING'
                
        except:
            return 'NEUTRAL'
    
    def get_recent_structure_signals(self, df: pd.DataFrame) -> Dict:
        """
        Son market yapısı sinyallerini al
        """
        try:
            structure = self.detect_market_structure(df)
            
            result = {
                'recent_sweep': None,
                'recent_choch': None,
                'recent_bos': None,
                'structure_bias': structure['market_structure'],
                'has_liquidity_taken': False,
                'structure_changed': False
            }
            
            # En son sweep
            if structure['liquidity_sweeps']:
                result['recent_sweep'] = structure['liquidity_sweeps'][0]
                result['has_liquidity_taken'] = True
            
            # En son CHoCH
            if structure['choch_signals']:
                result['recent_choch'] = structure['choch_signals'][0]
                result['structure_changed'] = True
            
            # En son BOS
            if structure['bos_signals']:
                result['recent_bos'] = structure['bos_signals'][0]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Recent structure signals error: {e}")
            return {
                'recent_sweep': None,
                'recent_choch': None,
                'recent_bos': None,
                'structure_bias': 'NEUTRAL',
                'has_liquidity_taken': False,
                'structure_changed': False
            }