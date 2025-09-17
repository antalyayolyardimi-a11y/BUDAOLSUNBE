"""
Advanced Risk Management System
1:1 R/R, 0.5R risk limiti, dinamik stop/TP hesaplaması
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

class RiskManagementSystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Risk parametreleri
        self.default_risk_reward = 1.0  # 1:1 R/R
        self.max_risk_reward = 3.0      # Maksimum 1:3
        self.contra_trend_risk = 0.5    # Karşı trend için 0.5R
        self.min_risk_reward = 0.8      # Minimum 1:0.8
        
    def calculate_position_sizing(self, entry_price: float, stop_loss: float, 
                                account_balance: float = 1000, risk_percent: float = 1.0) -> Dict:
        """
        Pozisyon büyüklüğü hesaplama
        """
        try:
            # Risk miktarı (account'un %1'i default)
            risk_amount = account_balance * (risk_percent / 100)
            
            # Stop distance
            stop_distance = abs(entry_price - stop_loss)
            
            if stop_distance == 0:
                return {'position_size': 0, 'risk_amount': 0, 'stop_distance': 0}
            
            # Position size hesaplama
            position_size = risk_amount / stop_distance
            
            return {
                'position_size': round(position_size, 6),
                'risk_amount': risk_amount,
                'stop_distance': stop_distance,
                'risk_percent': risk_percent
            }
            
        except Exception as e:
            self.logger.error(f"Position sizing calculation error: {e}")
            return {'position_size': 0, 'risk_amount': 0, 'stop_distance': 0}
    
    def calculate_stop_loss(self, signal_type: str, entry_price: float, 
                          structure_data: Dict, sweep_data: Optional[Dict] = None) -> float:
        """
        Stop loss seviyesi hesaplama
        """
        try:
            if signal_type.upper() == 'LONG':
                return self._calculate_long_stop_loss(entry_price, structure_data, sweep_data)
            else:
                return self._calculate_short_stop_loss(entry_price, structure_data, sweep_data)
                
        except Exception as e:
            self.logger.error(f"Stop loss calculation error: {e}")
            return entry_price * 0.98 if signal_type.upper() == 'LONG' else entry_price * 1.02
    
    def _calculate_long_stop_loss(self, entry_price: float, structure_data: Dict, 
                                sweep_data: Optional[Dict]) -> float:
        """
        LONG pozisyon için stop loss
        """
        try:
            stop_candidates = []
            
            # 1. Sweep fitilinin hemen altı (en güçlü)
            if sweep_data and sweep_data.get('type') == 'low_sweep':
                sweep_stop = sweep_data['sweep_price'] - (entry_price * 0.001)  # %0.1 buffer
                stop_candidates.append(('sweep_low', sweep_stop, 100))
            
            # 2. Son swing low
            if structure_data.get('swing_points', {}).get('lows'):
                recent_low = structure_data['swing_points']['lows'][-1]
                swing_stop = recent_low['price'] - (entry_price * 0.001)
                stop_candidates.append(('swing_low', swing_stop, 80))
            
            # 3. Momentum low (MOM-FTR için)
            if structure_data.get('momentum_low'):
                momentum_stop = structure_data['momentum_low'] - (entry_price * 0.001)
                stop_candidates.append(('momentum_low', momentum_stop, 70))
            
            # 4. Order Block/FVG low
            if structure_data.get('active_zones'):
                for zone in structure_data['active_zones']:
                    if 'bullish' in zone['type']:
                        zone_stop = zone['bottom'] - (entry_price * 0.001)
                        stop_candidates.append(('zone_low', zone_stop, 60))
            
            # En yakın ve mantıklı stop'u seç
            if stop_candidates:
                # Entry'den çok uzak olmayan ve mantıklı olanları filtrele
                valid_stops = []
                for name, price, strength in stop_candidates:
                    if price < entry_price:  # Stop entry'nin altında olmalı
                        stop_distance = (entry_price - price) / entry_price
                        if 0.005 <= stop_distance <= 0.05:  # %0.5 - %5 arası
                            valid_stops.append((name, price, strength))
                
                if valid_stops:
                    # En güçlü stop'u seç
                    best_stop = max(valid_stops, key=lambda x: x[2])
                    return best_stop[1]
            
            # Fallback: Entry'nin %2 altı
            return entry_price * 0.98
            
        except Exception as e:
            self.logger.error(f"Long stop loss calculation error: {e}")
            return entry_price * 0.98
    
    def _calculate_short_stop_loss(self, entry_price: float, structure_data: Dict, 
                                 sweep_data: Optional[Dict]) -> float:
        """
        SHORT pozisyon için stop loss
        """
        try:
            stop_candidates = []
            
            # 1. Sweep fitilinin hemen üstü (en güçlü)
            if sweep_data and sweep_data.get('type') == 'high_sweep':
                sweep_stop = sweep_data['sweep_price'] + (entry_price * 0.001)  # %0.1 buffer
                stop_candidates.append(('sweep_high', sweep_stop, 100))
            
            # 2. Son swing high
            if structure_data.get('swing_points', {}).get('highs'):
                recent_high = structure_data['swing_points']['highs'][-1]
                swing_stop = recent_high['price'] + (entry_price * 0.001)
                stop_candidates.append(('swing_high', swing_stop, 80))
            
            # 3. Momentum high (MOM-FTR için)
            if structure_data.get('momentum_high'):
                momentum_stop = structure_data['momentum_high'] + (entry_price * 0.001)
                stop_candidates.append(('momentum_high', momentum_stop, 70))
            
            # 4. Order Block/FVG high
            if structure_data.get('active_zones'):
                for zone in structure_data['active_zones']:
                    if 'bearish' in zone['type']:
                        zone_stop = zone['top'] + (entry_price * 0.001)
                        stop_candidates.append(('zone_high', zone_stop, 60))
            
            # En yakın ve mantıklı stop'u seç
            if stop_candidates:
                # Entry'den çok uzak olmayan ve mantıklı olanları filtrele
                valid_stops = []
                for name, price, strength in stop_candidates:
                    if price > entry_price:  # Stop entry'nin üstünde olmalı
                        stop_distance = (price - entry_price) / entry_price
                        if 0.005 <= stop_distance <= 0.05:  # %0.5 - %5 arası
                            valid_stops.append((name, price, strength))
                
                if valid_stops:
                    # En güçlü stop'u seç
                    best_stop = max(valid_stops, key=lambda x: x[2])
                    return best_stop[1]
            
            # Fallback: Entry'nin %2 üstü
            return entry_price * 1.02
            
        except Exception as e:
            self.logger.error(f"Short stop loss calculation error: {e}")
            return entry_price * 1.02
    
    def calculate_take_profits(self, signal_type: str, entry_price: float, stop_loss: float,
                             htf_bias: str, structure_data: Dict, risk_reward: Optional[float] = None) -> Dict:
        """
        Take profit seviyelerini hesapla
        """
        try:
            # Risk distance
            risk_distance = abs(entry_price - stop_loss)
            
            # Risk/Reward oranını belirle
            if risk_reward is None:
                # HTF bias ile uyumlu ise normal R/R, değilse düşük R/R
                if self._is_signal_with_htf_bias(signal_type, htf_bias):
                    target_rr = self.default_risk_reward
                else:
                    target_rr = self.contra_trend_risk
            else:
                target_rr = risk_reward
            
            # Temel TP seviyeleri
            if signal_type.upper() == 'LONG':
                tp1_price = entry_price + (risk_distance * target_rr)
                tp2_price = entry_price + (risk_distance * target_rr * 2)
            else:
                tp1_price = entry_price - (risk_distance * target_rr)
                tp2_price = entry_price - (risk_distance * target_rr * 2)
            
            # Struktur bazlı TP ayarlamaları
            tp1_price, tp2_price = self._adjust_tps_for_structure(
                signal_type, tp1_price, tp2_price, structure_data, entry_price
            )
            
            return {
                'tp1': round(tp1_price, 6),
                'tp2': round(tp2_price, 6),
                'risk_reward_1': target_rr,
                'risk_reward_2': target_rr * 2,
                'risk_distance': risk_distance,
                'tp1_distance': abs(tp1_price - entry_price),
                'tp2_distance': abs(tp2_price - entry_price)
            }
            
        except Exception as e:
            self.logger.error(f"Take profit calculation error: {e}")
            return self._fallback_take_profits(signal_type, entry_price, stop_loss)
    
    def _adjust_tps_for_structure(self, signal_type: str, tp1: float, tp2: float, 
                                structure_data: Dict, entry_price: float) -> Tuple[float, float]:
        """
        Yapısal seviyelere göre TP'leri ayarla
        """
        try:
            # Likidite seviyeleri
            liquidity_levels = structure_data.get('liquidity_levels', {})
            
            if signal_type.upper() == 'LONG':
                # Yukarıdaki dirençleri bul
                resistance_levels = []
                
                # Equal highs
                for level in liquidity_levels.get('equal_highs', []):
                    if level['price'] > entry_price:
                        resistance_levels.append(level['price'])
                
                # Previous highs
                for level in liquidity_levels.get('previous_highs', []):
                    if level['price'] > entry_price:
                        resistance_levels.append(level['price'])
                
                # En yakın dirençlere göre TP'leri ayarla
                if resistance_levels:
                    resistance_levels.sort()
                    
                    # TP1'i ilk dirence yakın ayarla
                    if resistance_levels[0] < tp1:
                        tp1 = resistance_levels[0] * 0.999  # %0.1 önce
                    
                    # TP2'yi ikinci dirence ayarla
                    if len(resistance_levels) > 1 and resistance_levels[1] < tp2:
                        tp2 = resistance_levels[1] * 0.999
            
            else:  # SHORT
                # Aşağıdaki destekleri bul
                support_levels = []
                
                # Equal lows
                for level in liquidity_levels.get('equal_lows', []):
                    if level['price'] < entry_price:
                        support_levels.append(level['price'])
                
                # Previous lows
                for level in liquidity_levels.get('previous_lows', []):
                    if level['price'] < entry_price:
                        support_levels.append(level['price'])
                
                # En yakın desteklere göre TP'leri ayarla
                if support_levels:
                    support_levels.sort(reverse=True)
                    
                    # TP1'i ilk desteğe yakın ayarla
                    if support_levels[0] > tp1:
                        tp1 = support_levels[0] * 1.001  # %0.1 sonra
                    
                    # TP2'yi ikinci desteğe ayarla
                    if len(support_levels) > 1 and support_levels[1] > tp2:
                        tp2 = support_levels[1] * 1.001
            
            return tp1, tp2
            
        except Exception as e:
            self.logger.error(f"TP structure adjustment error: {e}")
            return tp1, tp2
    
    def _is_signal_with_htf_bias(self, signal_type: str, htf_bias: str) -> bool:
        """
        Sinyal HTF bias ile uyumlu mu?
        """
        if htf_bias == 'BULLISH' and signal_type.upper() == 'LONG':
            return True
        elif htf_bias == 'BEARISH' and signal_type.upper() == 'SHORT':
            return True
        return False
    
    def _fallback_take_profits(self, signal_type: str, entry_price: float, stop_loss: float) -> Dict:
        """
        Fallback TP hesaplama
        """
        risk_distance = abs(entry_price - stop_loss)
        
        if signal_type.upper() == 'LONG':
            tp1 = entry_price + risk_distance
            tp2 = entry_price + (risk_distance * 2)
        else:
            tp1 = entry_price - risk_distance
            tp2 = entry_price - (risk_distance * 2)
        
        return {
            'tp1': round(tp1, 6),
            'tp2': round(tp2, 6),
            'risk_reward_1': 1.0,
            'risk_reward_2': 2.0,
            'risk_distance': risk_distance,
            'tp1_distance': risk_distance,
            'tp2_distance': risk_distance * 2
        }
    
    def validate_risk_parameters(self, entry_price: float, stop_loss: float, 
                               take_profits: Dict) -> Dict:
        """
        Risk parametrelerini doğrula
        """
        try:
            validation = {
                'valid': True,
                'warnings': [],
                'errors': []
            }
            
            # Stop loss kontrolü
            if stop_loss == entry_price:
                validation['errors'].append("Stop loss entry price ile aynı")
                validation['valid'] = False
            
            # Risk distance kontrolü
            risk_distance = abs(entry_price - stop_loss)
            risk_percent = risk_distance / entry_price * 100
            
            if risk_percent > 5.0:
                validation['warnings'].append(f"Risk çok yüksek: %{risk_percent:.2f}")
            elif risk_percent < 0.5:
                validation['warnings'].append(f"Risk çok düşük: %{risk_percent:.2f}")
            
            # TP kontrolü
            tp1 = take_profits.get('tp1', 0)
            tp2 = take_profits.get('tp2', 0)
            
            if tp1 == entry_price:
                validation['errors'].append("TP1 entry price ile aynı")
                validation['valid'] = False
            
            # Risk/Reward kontrolü
            rr1 = take_profits.get('risk_reward_1', 0)
            if rr1 < self.min_risk_reward:
                validation['warnings'].append(f"R/R çok düşük: 1:{rr1:.2f}")
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Risk validation error: {e}")
            return {
                'valid': False,
                'warnings': [],
                'errors': [f"Validation error: {str(e)}"]
            }
    
    def create_risk_summary(self, signal_type: str, entry_price: float, stop_loss: float,
                          take_profits: Dict, position_sizing: Dict) -> Dict:
        """
        Risk özetini oluştur
        """
        try:
            risk_distance = abs(entry_price - stop_loss)
            risk_percent = (risk_distance / entry_price) * 100
            
            return {
                'signal_type': signal_type.upper(),
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'tp1': take_profits.get('tp1', 0),
                'tp2': take_profits.get('tp2', 0),
                'risk_distance': risk_distance,
                'risk_percent': round(risk_percent, 3),
                'risk_reward_1': take_profits.get('risk_reward_1', 0),
                'risk_reward_2': take_profits.get('risk_reward_2', 0),
                'position_size': position_sizing.get('position_size', 0),
                'risk_amount': position_sizing.get('risk_amount', 0),
                'potential_profit_1': abs(take_profits.get('tp1', entry_price) - entry_price),
                'potential_profit_2': abs(take_profits.get('tp2', entry_price) - entry_price)
            }
            
        except Exception as e:
            self.logger.error(f"Risk summary creation error: {e}")
            return {}
    
    def calculate_comprehensive_risk(self, signal_data: Dict) -> Dict:
        """
        Kapsamlı risk hesaplama - Ana fonksiyon
        """
        try:
            signal_type = signal_data['signal_type']
            entry_price = signal_data['entry_price']
            structure_data = signal_data.get('structure_data', {})
            sweep_data = signal_data.get('sweep_data')
            htf_bias = signal_data.get('htf_bias', 'NEUTRAL')
            
            # Stop loss hesapla
            stop_loss = self.calculate_stop_loss(signal_type, entry_price, structure_data, sweep_data)
            
            # Take profits hesapla
            take_profits = self.calculate_take_profits(signal_type, entry_price, stop_loss, htf_bias, structure_data)
            
            # Position sizing
            position_sizing = self.calculate_position_sizing(entry_price, stop_loss)
            
            # Validasyon
            validation = self.validate_risk_parameters(entry_price, stop_loss, take_profits)
            
            # Özet
            risk_summary = self.create_risk_summary(signal_type, entry_price, stop_loss, take_profits, position_sizing)
            
            return {
                'stop_loss': stop_loss,
                'take_profits': take_profits,
                'position_sizing': position_sizing,
                'validation': validation,
                'risk_summary': risk_summary,
                'calculated_at': pd.Timestamp.now()
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive risk calculation error: {e}")
            return {}