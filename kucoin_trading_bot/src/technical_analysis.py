# SMC Trading Strategy
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional
from datetime import datetime

from strategies.multi_timeframe_analyzer import MultiTimeframeAnalyzer
from strategies.order_block_fvg_detector import OrderBlockFVGDetector
from strategies.momentum_reversal_detector import MomentumReversalDetector
from strategies.adx_directional_filter import ADXDirectionalFilter
from strategies.liquidity_sweep_detector import LiquiditySweepDetector
from strategies.risk_management import RiskManagementSystem

def generate_trading_signal(symbol: str, kucoin_api) -> Dict:
    try:
        logger = logging.getLogger(__name__)
        
        # Initialize strategy components
        mtf_analyzer = MultiTimeframeAnalyzer()
        ob_fvg_detector = OrderBlockFVGDetector()
        momentum_detector = MomentumReversalDetector()
        adx_filter = ADXDirectionalFilter()
        liquidity_detector = LiquiditySweepDetector()
        
        # Get multi-timeframe data
        mtf_data = mtf_analyzer.get_multi_timeframe_data(symbol, kucoin_api)
        
        if not mtf_data or len(mtf_data) < 2:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reason": "Insufficient data",
                "timestamp": datetime.now()
            }
        
        # Get M15 data for analysis
        m15_data = mtf_data.get("M15")
        if m15_data is None or len(m15_data) < 50:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reason": "M15 data insufficient",
                "timestamp": datetime.now()
            }
        
        # Check ADX strength
        adx_signal = adx_filter.get_adx_signal(m15_data, 25)
        if not adx_signal["adx_strong"]:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reason": f"ADX weak: {adx_signal["adx"]:.1f}",
                "timestamp": datetime.now()
            }
        
        # Get current price
        current_price = float(m15_data.iloc[-1]["close"])
        
        # Detect order blocks and FVGs
        order_blocks = ob_fvg_detector.detect_order_blocks(m15_data)
        fvgs = ob_fvg_detector.detect_fair_value_gaps(m15_data)
        zone_check = ob_fvg_detector.check_price_in_zones(current_price, order_blocks, fvgs)
        
        # Get momentum signals
        momentum_signals = momentum_detector.get_latest_signals(m15_data)
        
        # Analyze market structure
        recent_structure = liquidity_detector.get_recent_structure_signals(m15_data)
        
        # Determine best signal
        best_signal = None
        
        # Check SMC signals
        if (recent_structure["has_liquidity_taken"] and 
            recent_structure["recent_choch"] and
            adx_signal["long_allowed"] and
            (zone_check["in_bullish_ob"] or zone_check["in_bullish_fvg"])):
            
            best_signal = {
                "type": "SMC",
                "signal": "LONG",
                "strength": 80,
                "entry_price": current_price
            }
        
        elif (recent_structure["has_liquidity_taken"] and 
              recent_structure["recent_choch"] and
              adx_signal["short_allowed"] and
              (zone_check["in_bearish_ob"] or zone_check["in_bearish_fvg"])):
            
            best_signal = {
                "type": "SMC",
                "signal": "SHORT",
                "strength": 80,
                "entry_price": current_price
            }
        
        # Check momentum signals
        elif momentum_signals["has_bullish_signal"] and adx_signal["long_allowed"]:
            best_signal = {
                "type": "MOM-FTR",
                "signal": "LONG",
                "strength": momentum_signals["bullish_signal"]["strength"],
                "entry_price": momentum_signals["bullish_signal"]["entry_price"]
            }
        
        elif momentum_signals["has_bearish_signal"] and adx_signal["short_allowed"]:
            best_signal = {
                "type": "MOM-FTR",
                "signal": "SHORT",
                "strength": momentum_signals["bearish_signal"]["strength"],
                "entry_price": momentum_signals["bearish_signal"]["entry_price"]
            }
        
        if not best_signal or best_signal["strength"] < 70:
            return {
                "signal": "HOLD",
                "confidence": 0,
                "reason": "No strong signal found",
                "timestamp": datetime.now()
            }
        
        # Calculate risk levels with proper TP/SL ratios
        signal_type = best_signal["signal"]
        entry_price = best_signal["entry_price"]
        
        # Dynamic risk/reward calculation based on volatility
        volatility = np.std(m15_data['close'].tail(20)) / np.mean(m15_data['close'].tail(20))
        base_risk_percent = max(0.015, min(0.05, volatility * 2))  # 1.5% - 5% risk
        
        if signal_type == "LONG":
            stop_loss = entry_price * (1 - base_risk_percent)
            # Progressive take profits
            tp1 = entry_price * (1 + base_risk_percent * 1.5)    # 1:1.5 R/R
            tp2 = entry_price * (1 + base_risk_percent * 2.5)    # 1:2.5 R/R  
            tp3 = entry_price * (1 + base_risk_percent * 4.0)    # 1:4 R/R
        else:  # SHORT
            stop_loss = entry_price * (1 + base_risk_percent)
            # Progressive take profits for SHORT
            tp1 = entry_price * (1 - base_risk_percent * 1.5)    # 1:1.5 R/R
            tp2 = entry_price * (1 - base_risk_percent * 2.5)    # 1:2.5 R/R
            tp3 = entry_price * (1 - base_risk_percent * 4.0)    # 1:4 R/R
        
        # Calculate actual risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(entry_price - tp1)
        risk_reward_ratio = reward / risk if risk > 0 else 1.0
        
        return {
            "signal": signal_type,
            "confidence": best_signal["strength"],
            "entry_price": round(entry_price, 6),
            "stop_loss": round(stop_loss, 6),
            "take_profit_1": round(tp1, 6),
            "take_profit_2": round(tp2, 6),
            "take_profit_3": round(tp3, 6),
            "take_profits": {
                "tp1": round(tp1, 6),
                "tp2": round(tp2, 6), 
                "tp3": round(tp3, 6)
            },
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "volatility": round(volatility * 100, 2),
            "reason": f"{best_signal["type"]} Strategy",
            "analysis": f"🎯 {best_signal["type"]} {signal_type}\n💪 Strength: {best_signal["strength"]:.1f}\n⚡ ADX: {adx_signal["adx"]:.1f}\n📊 R/R: 1:{risk_reward_ratio:.1f}",
            "timestamp": datetime.now(),
            "strength": best_signal["strength"]
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Trading signal error for {symbol}: {e}")
        return {
            "signal": "HOLD",
            "confidence": 0,
            "reason": f"Analysis error: {str(e)}",
            "timestamp": datetime.now()
        }
