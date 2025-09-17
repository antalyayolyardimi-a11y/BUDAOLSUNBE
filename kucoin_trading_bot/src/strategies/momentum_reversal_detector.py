"""
Momentum Failure to Return (MOM-FTR) Strategy
3+ ardışık momentum + tersleme pattern tespiti
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

class MomentumReversalDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_momentum_reversal(self, df: pd.DataFrame, min_consecutive: int = 3) -> Dict:
        """
        Momentum tersleme pattern tespiti
        """
        try:
            signals = {
                'bullish_reversal': [],
                'bearish_reversal': []
            }
            
            if len(df) < min_consecutive + 3:
                return signals
            
            # Son 20 mumda pattern ara
            recent_data = df.tail(20)
            
            for i in range(min_consecutive + 2, len(recent_data)):
                current_idx = i
                
                # Bullish reversal pattern
                bullish_pattern = self._detect_bullish_momentum_reversal(recent_data, current_idx, min_consecutive)
                if bullish_pattern:
                    signals['bullish_reversal'].append(bullish_pattern)
                
                # Bearish reversal pattern
                bearish_pattern = self._detect_bearish_momentum_reversal(recent_data, current_idx, min_consecutive)
                if bearish_pattern:
                    signals['bearish_reversal'].append(bearish_pattern)
            
            # En son ve en güçlü sinyalleri al
            if signals['bullish_reversal']:
                signals['bullish_reversal'] = sorted(
                    signals['bullish_reversal'], 
                    key=lambda x: (x['timestamp'], x['strength']), 
                    reverse=True
                )[:3]
            
            if signals['bearish_reversal']:
                signals['bearish_reversal'] = sorted(
                    signals['bearish_reversal'], 
                    key=lambda x: (x['timestamp'], x['strength']), 
                    reverse=True
                )[:3]
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Momentum reversal detection error: {e}")
            return {'bullish_reversal': [], 'bearish_reversal': []}
    
    def _detect_bullish_momentum_reversal(self, df: pd.DataFrame, current_idx: int, min_consecutive: int) -> Optional[Dict]:
        """
        Bullish Momentum Reversal Pattern:
        1. En az 3 ardışık kırmızı mum (güçlü düşüş)
        2. 1-2 küçük gövdeli nötr mum (momentum zayıflıyor)
        3. Güçlü yeşil mum (tersleme konfirmasyonu)
        """
        try:
            if current_idx < min_consecutive + 2:
                return None
            
            current_candle = df.iloc[current_idx]
            
            # 3. Mevcut mum güçlü bullish olmalı
            if not current_candle['is_bullish']:
                return None
            
            # Güçlü bullish mum kriterleri
            avg_body = df['body_size'].rolling(10).mean().iloc[current_idx]
            if current_candle['body_size'] < avg_body * 1.2:
                return None
            
            # 2. Önceki 1-2 mum küçük gövdeli/nötr olmalı
            transition_candles = []
            transition_start = current_idx - 1
            
            for j in range(1, 3):  # Son 2 mumu kontrol et
                if current_idx - j >= 0:
                    candle = df.iloc[current_idx - j]
                    if candle['body_size'] < avg_body * 0.5:  # Küçük gövde
                        transition_candles.append(candle)
                        transition_start = current_idx - j
                    else:
                        break
            
            if not transition_candles:
                return None
            
            # 1. Geçiş mumlarından önce ardışık bearish mumlar
            consecutive_bearish = 0
            bearish_start_idx = transition_start - 1
            
            for j in range(transition_start - 1, max(transition_start - min_consecutive - 2, -1), -1):
                if j >= 0:
                    candle = df.iloc[j]
                    if candle['is_bearish'] and candle['body_size'] > avg_body * 0.7:
                        consecutive_bearish += 1
                        bearish_start_idx = j
                    else:
                        break
                        
            if consecutive_bearish < min_consecutive:
                return None
            
            # Pattern gücünü hesapla
            strength = self._calculate_reversal_strength(
                df, bearish_start_idx, transition_start, current_idx, 'bullish'
            )
            
            return {
                'type': 'bullish_momentum_reversal',
                'timestamp': df.index[current_idx],
                'entry_price': current_candle['close'],
                'consecutive_count': consecutive_bearish,
                'transition_count': len(transition_candles),
                'strength': strength,
                'momentum_low': df.iloc[bearish_start_idx:transition_start+1]['low'].min(),
                'reversal_candle': {
                    'open': current_candle['open'],
                    'close': current_candle['close'],
                    'high': current_candle['high'],
                    'low': current_candle['low'],
                    'body_size': current_candle['body_size']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Bullish momentum reversal detection error: {e}")
            return None
    
    def _detect_bearish_momentum_reversal(self, df: pd.DataFrame, current_idx: int, min_consecutive: int) -> Optional[Dict]:
        """
        Bearish Momentum Reversal Pattern:
        1. En az 3 ardışık yeşil mum (güçlü yükseliş)
        2. 1-2 küçük gövdeli nötr mum (momentum zayıflıyor)
        3. Güçlü kırmızı mum (tersleme konfirmasyonu)
        """
        try:
            if current_idx < min_consecutive + 2:
                return None
            
            current_candle = df.iloc[current_idx]
            
            # 3. Mevcut mum güçlü bearish olmalı
            if not current_candle['is_bearish']:
                return None
            
            # Güçlü bearish mum kriterleri
            avg_body = df['body_size'].rolling(10).mean().iloc[current_idx]
            if current_candle['body_size'] < avg_body * 1.2:
                return None
            
            # 2. Önceki 1-2 mum küçük gövdeli/nötr olmalı
            transition_candles = []
            transition_start = current_idx - 1
            
            for j in range(1, 3):  # Son 2 mumu kontrol et
                if current_idx - j >= 0:
                    candle = df.iloc[current_idx - j]
                    if candle['body_size'] < avg_body * 0.5:  # Küçük gövde
                        transition_candles.append(candle)
                        transition_start = current_idx - j
                    else:
                        break
            
            if not transition_candles:
                return None
            
            # 1. Geçiş mumlarından önce ardışık bullish mumlar
            consecutive_bullish = 0
            bullish_start_idx = transition_start - 1
            
            for j in range(transition_start - 1, max(transition_start - min_consecutive - 2, -1), -1):
                if j >= 0:
                    candle = df.iloc[j]
                    if candle['is_bullish'] and candle['body_size'] > avg_body * 0.7:
                        consecutive_bullish += 1
                        bullish_start_idx = j
                    else:
                        break
                        
            if consecutive_bullish < min_consecutive:
                return None
            
            # Pattern gücünü hesapla
            strength = self._calculate_reversal_strength(
                df, bullish_start_idx, transition_start, current_idx, 'bearish'
            )
            
            return {
                'type': 'bearish_momentum_reversal',
                'timestamp': df.index[current_idx],
                'entry_price': current_candle['close'],
                'consecutive_count': consecutive_bullish,
                'transition_count': len(transition_candles),
                'strength': strength,
                'momentum_high': df.iloc[bullish_start_idx:transition_start+1]['high'].max(),
                'reversal_candle': {
                    'open': current_candle['open'],
                    'close': current_candle['close'],
                    'high': current_candle['high'],
                    'low': current_candle['low'],
                    'body_size': current_candle['body_size']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Bearish momentum reversal detection error: {e}")
            return None
    
    def _calculate_reversal_strength(self, df: pd.DataFrame, momentum_start: int, transition_start: int, 
                                   current_idx: int, reversal_type: str) -> float:
        """
        Momentum reversal pattern gücünü hesapla (0-100)
        """
        try:
            strength = 0
            
            # 1. Ardışık mum sayısı (25 puan)
            consecutive_count = transition_start - momentum_start
            if consecutive_count >= 5:
                strength += 25
            elif consecutive_count >= 4:
                strength += 20
            elif consecutive_count >= 3:
                strength += 15
            
            # 2. Momentum gücü (30 puan)
            if reversal_type == 'bullish':
                momentum_range = df.iloc[momentum_start]['high'] - df.iloc[transition_start]['low']
            else:
                momentum_range = df.iloc[transition_start]['high'] - df.iloc[momentum_start]['low']
            
            avg_range = df['true_range'].rolling(10).mean().iloc[current_idx]
            momentum_strength = momentum_range / (avg_range * consecutive_count)
            
            if momentum_strength > 1.5:
                strength += 30
            elif momentum_strength > 1.0:
                strength += 20
            elif momentum_strength > 0.5:
                strength += 10
            
            # 3. Tersleme mumunun gücü (25 puan)
            current_candle = df.iloc[current_idx]
            avg_body = df['body_size'].rolling(10).mean().iloc[current_idx]
            reversal_strength = current_candle['body_size'] / avg_body
            
            if reversal_strength > 2.0:
                strength += 25
            elif reversal_strength > 1.5:
                strength += 20
            elif reversal_strength > 1.2:
                strength += 15
            
            # 4. Hacim konfirmasyonu (20 puan)
            avg_volume = df['volume'].rolling(10).mean().iloc[current_idx]
            if current_candle['volume'] > avg_volume * 1.5:
                strength += 20
            elif current_candle['volume'] > avg_volume:
                strength += 10
            
            return min(strength, 100)
            
        except Exception as e:
            self.logger.error(f"Reversal strength calculation error: {e}")
            return 0
    
    def get_latest_signals(self, df: pd.DataFrame) -> Dict:
        """
        En son momentum reversal sinyallerini al
        """
        try:
            signals = self.detect_momentum_reversal(df)
            
            result = {
                'has_bullish_signal': False,
                'has_bearish_signal': False,
                'bullish_signal': None,
                'bearish_signal': None
            }
            
            # En son bullish signal
            if signals['bullish_reversal']:
                latest_bullish = signals['bullish_reversal'][0]
                # Son 5 mum içinde olmalı
                recent_timestamp = df.index[-5] if len(df) >= 5 else df.index[0]
                
                if latest_bullish['timestamp'] >= recent_timestamp:
                    result['has_bullish_signal'] = True
                    result['bullish_signal'] = latest_bullish
            
            # En son bearish signal
            if signals['bearish_reversal']:
                latest_bearish = signals['bearish_reversal'][0]
                # Son 5 mum içinde olmalı
                recent_timestamp = df.index[-5] if len(df) >= 5 else df.index[0]
                
                if latest_bearish['timestamp'] >= recent_timestamp:
                    result['has_bearish_signal'] = True
                    result['bearish_signal'] = latest_bearish
            
            return result
            
        except Exception as e:
            self.logger.error(f"Latest signals error: {e}")
            return {
                'has_bullish_signal': False,
                'has_bearish_signal': False,
                'bullish_signal': None,
                'bearish_signal': None
            }
    
    def validate_momentum_pattern(self, signal: Dict, df: pd.DataFrame) -> bool:
        """
        Momentum pattern validasyonu
        """
        try:
            if not signal:
                return False
            
            # Minimum güç kontrolü
            if signal['strength'] < 60:
                return False
            
            # Ardışık mum sayısı kontrolü
            if signal['consecutive_count'] < 3:
                return False
            
            # Tersleme mumunun gücü kontrolü
            avg_body = df['body_size'].rolling(10).mean().iloc[-1]
            if signal['reversal_candle']['body_size'] < avg_body * 1.2:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Momentum pattern validation error: {e}")
            return False