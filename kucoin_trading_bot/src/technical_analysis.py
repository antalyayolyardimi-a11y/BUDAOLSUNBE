import pandas as pd
import numpy as np
import ta
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from kucoin_api import KuCoinAPI

class TechnicalAnalyzer:
    def __init__(self, kucoin_api: KuCoinAPI):
        self.api = kucoin_api
        self.logger = logging.getLogger(__name__)
        
    def klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """KuCoin klines verisini DataFrame'e çevir"""
        if not klines:
            return pd.DataFrame()
            
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'close', 'high', 'low', 'volume', 'turnover'
        ])
        
        # Veri tiplerini düzelt
        df['timestamp'] = pd.to_datetime(pd.to_numeric(df['timestamp'], errors='coerce'), unit='s')
        for col in ['open', 'close', 'high', 'low', 'volume', 'turnover']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df.set_index('timestamp', inplace=True)
        return df
        
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """RSI hesapla"""
        return ta.momentum.RSIIndicator(df['close'], window=period).rsi()
        
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD hesapla"""
        macd_indicator = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
        return {
            'macd': macd_indicator.macd(),
            'signal': macd_indicator.macd_signal(),
            'histogram': macd_indicator.macd_diff()
        }
        
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands hesapla"""
        bb_indicator = ta.volatility.BollingerBands(df['close'], window=period, window_dev=std)
        return {
            'upper': bb_indicator.bollinger_hband(),
            'middle': bb_indicator.bollinger_mavg(),
            'lower': bb_indicator.bollinger_lband()
        }
        
    def calculate_volume_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Volume indikatörleri hesapla"""
        return {
            'volume_sma': df['volume'].rolling(window=20).mean(),  # Basit volume SMA
            'volume_obv': ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume(),
            'volume_cmf': ta.volume.ChaikinMoneyFlowIndicator(df['high'], df['low'], df['close'], df['volume']).chaikin_money_flow()
        }
        
    def calculate_support_resistance(self, df: pd.DataFrame, lookback: int = 20) -> Dict[str, float]:
        """Destek ve direnç seviyelerini hesapla"""
        recent_data = df.tail(lookback)
        
        # Pivot noktaları bul
        highs = recent_data['high'].rolling(window=3, center=True).max()
        lows = recent_data['low'].rolling(window=3, center=True).min()
        
        # Pivot high'lar (direnç)
        pivot_highs = recent_data[recent_data['high'] == highs]['high'].values
        # Pivot low'lar (destek)
        pivot_lows = recent_data[recent_data['low'] == lows]['low'].values
        
        resistance = np.mean(pivot_highs) if len(pivot_highs) > 0 else recent_data['high'].max()
        support = np.mean(pivot_lows) if len(pivot_lows) > 0 else recent_data['low'].min()
        
        return {
            'resistance': resistance,
            'support': support
        }
        
    def calculate_trend_strength(self, df: pd.DataFrame) -> Dict[str, float]:
        """Trend gücünü hesapla"""
        # ADX hesapla
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
        
        # EMA'lar arası ilişki
        ema_9 = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
        ema_21 = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
        ema_50 = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        
        # Trend yönü (1: yukarı, -1: aşağı, 0: yatay)
        if ema_9.iloc[-1] > ema_21.iloc[-1] > ema_50.iloc[-1]:
            trend_direction = 1
        elif ema_9.iloc[-1] < ema_21.iloc[-1] < ema_50.iloc[-1]:
            trend_direction = -1
        else:
            trend_direction = 0
            
        return {
            'adx': adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0,
            'trend_direction': trend_direction,
            'ema_9': ema_9.iloc[-1],
            'ema_21': ema_21.iloc[-1],
            'ema_50': ema_50.iloc[-1]
        }
        
    def analyze_coin(self, symbol: str, interval: str = '15min') -> Optional[Dict]:
        """Coin için komple teknik analiz"""
        try:
            # Veri çek (son 200 mum)
            klines = self.api.get_klines(symbol, interval)
            if len(klines) < 50:
                self.logger.warning(f"Yetersiz veri: {symbol}")
                return None
                
            df = self.klines_to_dataframe(klines)
            if df.empty:
                return None
                
            # Temel indikatörler
            rsi = self.calculate_rsi(df)
            macd = self.calculate_macd(df)
            bb = self.calculate_bollinger_bands(df)
            volume_indicators = self.calculate_volume_indicators(df)
            support_resistance = self.calculate_support_resistance(df)
            trend = self.calculate_trend_strength(df)
            
            # Mevcut değerler
            current_price = df['close'].iloc[-1]
            current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
            current_macd = macd['macd'].iloc[-1] if not pd.isna(macd['macd'].iloc[-1]) else 0
            current_signal = macd['signal'].iloc[-1] if not pd.isna(macd['signal'].iloc[-1]) else 0
            
            # BB pozisyon
            bb_position = (current_price - bb['lower'].iloc[-1]) / (bb['upper'].iloc[-1] - bb['lower'].iloc[-1])
            
            # Sinyal gücü hesaplama
            signal_strength = self._calculate_signal_strength({
                'rsi': current_rsi,
                'macd_histogram': macd['histogram'].iloc[-1],
                'bb_position': bb_position,
                'trend_strength': trend['adx'],
                'volume_ratio': volume_indicators['volume_cmf'].iloc[-1] if not pd.isna(volume_indicators['volume_cmf'].iloc[-1]) else 0
            })
            
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'indicators': {
                    'rsi': current_rsi,
                    'macd': {
                        'macd': current_macd,
                        'signal': current_signal,
                        'histogram': macd['histogram'].iloc[-1]
                    },
                    'bollinger_bands': {
                        'upper': bb['upper'].iloc[-1],
                        'middle': bb['middle'].iloc[-1],
                        'lower': bb['lower'].iloc[-1],
                        'position': bb_position
                    },
                    'volume': {
                        'cmf': volume_indicators['volume_cmf'].iloc[-1],
                        'obv': volume_indicators['volume_obv'].iloc[-1]
                    }
                },
                'support_resistance': support_resistance,
                'trend': trend,
                'signal_strength': signal_strength
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Analiz hatası {symbol}: {e}")
            return None
            
    def _calculate_signal_strength(self, indicators: Dict) -> Dict[str, float]:
        """Sinyal gücünü hesapla"""
        long_score = 0
        short_score = 0
        
        # RSI sinyalleri
        if indicators['rsi'] < 30:
            long_score += 2
        elif indicators['rsi'] < 40:
            long_score += 1
        elif indicators['rsi'] > 70:
            short_score += 2
        elif indicators['rsi'] > 60:
            short_score += 1
            
        # MACD sinyalleri
        if indicators['macd_histogram'] > 0:
            long_score += 1.5
        else:
            short_score += 1.5
            
        # Bollinger Bands
        if indicators['bb_position'] < 0.2:
            long_score += 1
        elif indicators['bb_position'] > 0.8:
            short_score += 1
            
        # Trend gücü
        if indicators['trend_strength'] > 25:
            if indicators.get('trend_direction', 0) == 1:
                long_score += 1
            elif indicators.get('trend_direction', 0) == -1:
                short_score += 1
                
        # Volume konfirmasyonu
        if indicators['volume_ratio'] > 0.1:
            long_score += 0.5
        elif indicators['volume_ratio'] < -0.1:
            short_score += 0.5
            
        return {
            'long_score': long_score,
            'short_score': short_score,
            'dominant_signal': 'LONG' if long_score > short_score else 'SHORT' if short_score > long_score else 'NEUTRAL'
        }
        
    def generate_trading_signal(self, analysis: Dict) -> Optional[Dict]:
        """Trading sinyali üret"""
        if not analysis:
            return None
            
        signal_strength = analysis['signal_strength']
        indicators = analysis['indicators']
        current_price = analysis['current_price']
        support_resistance = analysis['support_resistance']
        
        # Minimum sinyal gücü kontrolü
        min_score = 3.0
        if max(signal_strength['long_score'], signal_strength['short_score']) < min_score:
            return None
            
        signal_type = signal_strength['dominant_signal']
        if signal_type == 'NEUTRAL':
            return None
            
        # Stop loss ve take profit hesapla
        if signal_type == 'LONG':
            stop_loss = support_resistance['support'] * 0.98
            take_profit_1 = current_price * 1.02
            take_profit_2 = current_price * 1.04
            take_profit_3 = support_resistance['resistance'] * 0.98
        else:  # SHORT
            stop_loss = support_resistance['resistance'] * 1.02
            take_profit_1 = current_price * 0.98
            take_profit_2 = current_price * 0.96
            take_profit_3 = support_resistance['support'] * 1.02
            
        # Risk/Reward oranı kontrolü
        risk = abs(current_price - stop_loss) / current_price
        reward = abs(take_profit_1 - current_price) / current_price
        
        if risk == 0 or reward / risk < 1.5:
            return None
            
        signal = {
            'symbol': analysis['symbol'],
            'signal_type': signal_type,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profits': {
                'tp1': take_profit_1,
                'tp2': take_profit_2,
                'tp3': take_profit_3
            },
            'signal_strength': signal_strength,
            'risk_reward_ratio': reward / risk,
            'confidence': min(max(signal_strength['long_score'], signal_strength['short_score']) / 6 * 100, 95),
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        }
        
        return signal