"""
Multi-Timeframe Data Handler
HTF: H1 (Bias belirleme) 
LTF: M15 (Sinyal üretimi)
Mikro: M5 (2 mumluk tepki takibi)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

class MultiTimeframeAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Timeframe mapping - KuCoin API format
        self.timeframes = {
            'H1': '1hour',
            'M15': '15min', 
            'M5': '5min'
        }
        
        # Store data for each timeframe
        self.data_cache = {
            'H1': {},
            'M15': {},
            'M5': {}
        }
        
        # Cache validity (minutes)
        self.cache_validity = {
            'H1': 30,  # 30 dakika
            'M15': 8,  # 8 dakika
            'M5': 3    # 3 dakika
        }
        
    def get_multi_timeframe_data(self, symbol: str, kucoin_api) -> Dict:
        """
        Sembol için H1, M15, M5 verilerini al
        """
        try:
            result = {}
            
            for tf_name, tf_value in self.timeframes.items():
                # Cache kontrolü
                if self._is_cache_valid(symbol, tf_name):
                    result[tf_name] = self.data_cache[tf_name][symbol]['data']
                    continue
                
                # Yeni veri çek
                if tf_name == 'H1':
                    limit = 100  # H1 için 100 mum (4+ gün)
                elif tf_name == 'M15':
                    limit = 200  # M15 için 200 mum (50 saat)
                else:  # M5
                    limit = 100  # M5 için 100 mum (8+ saat)
                
                klines = kucoin_api.get_klines(symbol, tf_value, limit)
                
                if not klines:
                    self.logger.warning(f"{symbol} {tf_name} verisi alınamadı")
                    continue
                
                # DataFrame'e çevir
                df = self._process_klines(klines)
                
                if df is not None and len(df) > 0:
                    result[tf_name] = df
                    
                    # Cache'e kaydet
                    self.data_cache[tf_name][symbol] = {
                        'data': df,
                        'timestamp': datetime.now()
                    }
                    
                    self.logger.debug(f"{symbol} {tf_name}: {len(df)} mum verisi alındı")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Multi-timeframe data hatası ({symbol}): {e}")
            return {}
    
    def _process_klines(self, klines: List) -> Optional[pd.DataFrame]:
        """
        KuCoin klines verisini DataFrame'e çevir
        """
        try:
            if not klines:
                return None
                
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'turnover'])
            
            # Veri tiplerini düzenle
            df['timestamp'] = pd.to_datetime(pd.to_numeric(df['timestamp'], errors='coerce'), unit='s')
            df['open'] = pd.to_numeric(df['open'])
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Index'i timestamp yap
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Teknik göstergeler ekle
            df = self._add_basic_indicators(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Klines işleme hatası: {e}")
            return None
    
    def _add_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Temel teknik göstergeleri ekle
        """
        try:
            # Higher Highs, Higher Lows, Lower Highs, Lower Lows için
            df['prev_high'] = df['high'].shift(1)
            df['prev_low'] = df['low'].shift(1)
            df['prev_close'] = df['close'].shift(1)
            
            # Mum türleri
            df['is_bullish'] = df['close'] > df['open']
            df['is_bearish'] = df['close'] < df['open']
            df['body_size'] = abs(df['close'] - df['open'])
            df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
            
            # Volatilite
            df['true_range'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['prev_close']),
                    abs(df['low'] - df['prev_close'])
                )
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Temel göstergeler hatası: {e}")
            return df
    
    def _is_cache_valid(self, symbol: str, timeframe: str) -> bool:
        """
        Cache geçerliliğini kontrol et
        """
        try:
            if timeframe not in self.data_cache:
                return False
                
            if symbol not in self.data_cache[timeframe]:
                return False
                
            cache_time = self.data_cache[timeframe][symbol]['timestamp']
            validity_minutes = self.cache_validity[timeframe]
            
            return (datetime.now() - cache_time).total_seconds() < (validity_minutes * 60)
            
        except:
            return False
    
    def get_structure_bias(self, h1_data: pd.DataFrame) -> str:
        """
        H1 zaman diliminde yapı bias'ını belirle
        HH-HL = BULLISH
        LL-LH = BEARISH
        """
        try:
            if len(h1_data) < 20:
                return "NEUTRAL"
            
            # Son 20 mumda swing yüksek/alçak noktaları bul
            highs = []
            lows = []
            
            for i in range(5, len(h1_data) - 5):
                # Swing high kontrolü
                if (h1_data.iloc[i]['high'] > h1_data.iloc[i-1]['high'] and 
                    h1_data.iloc[i]['high'] > h1_data.iloc[i-2]['high'] and
                    h1_data.iloc[i]['high'] > h1_data.iloc[i+1]['high'] and
                    h1_data.iloc[i]['high'] > h1_data.iloc[i+2]['high']):
                    highs.append({
                        'price': h1_data.iloc[i]['high'],
                        'index': i,
                        'timestamp': h1_data.index[i]
                    })
                
                # Swing low kontrolü
                if (h1_data.iloc[i]['low'] < h1_data.iloc[i-1]['low'] and 
                    h1_data.iloc[i]['low'] < h1_data.iloc[i-2]['low'] and
                    h1_data.iloc[i]['low'] < h1_data.iloc[i+1]['low'] and
                    h1_data.iloc[i]['low'] < h1_data.iloc[i+2]['low']):
                    lows.append({
                        'price': h1_data.iloc[i]['low'],
                        'index': i,
                        'timestamp': h1_data.index[i]
                    })
            
            # Son 2 swing high ve low'u karşılaştır
            if len(highs) >= 2 and len(lows) >= 2:
                recent_highs = sorted(highs, key=lambda x: x['timestamp'])[-2:]
                recent_lows = sorted(lows, key=lambda x: x['timestamp'])[-2:]
                
                # Higher Highs ve Higher Lows kontrolü
                hh = recent_highs[1]['price'] > recent_highs[0]['price']
                hl = recent_lows[1]['price'] > recent_lows[0]['price']
                
                # Lower Lows ve Lower Highs kontrolü  
                ll = recent_lows[1]['price'] < recent_lows[0]['price']
                lh = recent_highs[1]['price'] < recent_highs[0]['price']
                
                if hh and hl:
                    return "BULLISH"
                elif ll and lh:
                    return "BEARISH"
            
            return "NEUTRAL"
            
        except Exception as e:
            self.logger.error(f"Structure bias hatası: {e}")
            return "NEUTRAL"
    
    def find_liquidity_levels(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Likidite seviyelerini bul (Equal highs/lows, Previous highs/lows)
        """
        try:
            levels = {
                'equal_highs': [],
                'equal_lows': [],
                'previous_highs': [],
                'previous_lows': []
            }
            
            if len(df) < lookback:
                return levels
            
            # Son lookback period'daki verileri al
            recent_data = df.tail(lookback)
            
            # Equal highs/lows bul (tolerance: %0.1)
            tolerance = 0.001  # %0.1
            
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            
            for i in range(len(highs)):
                current_high = highs[i]
                current_low = lows[i]
                
                # Equal highs
                for j in range(i+1, len(highs)):
                    if abs(highs[j] - current_high) / current_high <= tolerance:
                        levels['equal_highs'].append({
                            'price': current_high,
                            'count': 2,
                            'first_time': recent_data.index[i],
                            'last_time': recent_data.index[j]
                        })
                
                # Equal lows
                for j in range(i+1, len(lows)):
                    if abs(lows[j] - current_low) / current_low <= tolerance:
                        levels['equal_lows'].append({
                            'price': current_low,
                            'count': 2,
                            'first_time': recent_data.index[i],
                            'last_time': recent_data.index[j]
                        })
            
            # Previous major highs/lows
            for i in range(5, len(recent_data) - 5):
                high_val = recent_data.iloc[i]['high']
                low_val = recent_data.iloc[i]['low']
                
                # Previous high (pivot high)
                is_pivot_high = True
                for j in range(i-5, i+6):
                    if j != i and recent_data.iloc[j]['high'] >= high_val:
                        is_pivot_high = False
                        break
                
                if is_pivot_high:
                    levels['previous_highs'].append({
                        'price': high_val,
                        'timestamp': recent_data.index[i]
                    })
                
                # Previous low (pivot low)
                is_pivot_low = True
                for j in range(i-5, i+6):
                    if j != i and recent_data.iloc[j]['low'] <= low_val:
                        is_pivot_low = False
                        break
                
                if is_pivot_low:
                    levels['previous_lows'].append({
                        'price': low_val,
                        'timestamp': recent_data.index[i]
                    })
            
            return levels
            
        except Exception as e:
            self.logger.error(f"Likidite seviyesi hatası: {e}")
            return {'equal_highs': [], 'equal_lows': [], 'previous_highs': [], 'previous_lows': []}