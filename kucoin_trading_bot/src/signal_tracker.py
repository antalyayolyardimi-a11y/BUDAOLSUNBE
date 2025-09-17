import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from kucoin_api import KuCoinAPI
from telegram_bot import TelegramBot

class SignalStatus(Enum):
    ACTIVE = "active"
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    TP3_HIT = "tp3_hit"
    STOP_LOSS = "stop_loss"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class TrackedSignal:
    signal_id: str
    symbol: str
    signal_type: str
    entry_price: float
    current_price: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    status: SignalStatus
    created_at: datetime
    updated_at: datetime
    hit_tp_levels: List[int]
    max_profit_percentage: float
    max_loss_percentage: float
    notifications_sent: List[str]
    analysis_data: Dict
    
class SignalTracker:
    def __init__(self, kucoin_api: KuCoinAPI, telegram_bot: TelegramBot):
        self.api = kucoin_api
        self.telegram_bot = telegram_bot
        self.logger = logging.getLogger(__name__)
        
        self.active_signals: Dict[str, TrackedSignal] = {}
        self.completed_signals: List[TrackedSignal] = []
        self.signal_history_file = 'data/signal_history.json'
        self.active_signals_file = 'data/active_signals.json'
        
        # Tracking ayarları
        self.max_signal_age_hours = 24
        self.price_check_interval = 30  # saniye
        self.max_active_signals = 20
        
    def create_signal(self, signal_data: Dict) -> str:
        """Yeni sinyal oluştur ve takibe başla"""
        try:
            signal_id = str(uuid.uuid4())
            
            tracked_signal = TrackedSignal(
                signal_id=signal_id,
                symbol=signal_data['symbol'],
                signal_type=signal_data['signal_type'],
                entry_price=signal_data['entry_price'],
                current_price=signal_data['entry_price'],
                stop_loss=signal_data['stop_loss'],
                tp1=signal_data['take_profits']['tp1'],
                tp2=signal_data['take_profits']['tp2'],
                tp3=signal_data['take_profits']['tp3'],
                status=SignalStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                hit_tp_levels=[],
                max_profit_percentage=0.0,
                max_loss_percentage=0.0,
                notifications_sent=[],
                analysis_data=signal_data.get('analysis', {})
            )
            
            self.active_signals[signal_id] = tracked_signal
            self._save_active_signals()
            
            self.logger.info(f"Yeni sinyal oluşturuldu: {signal_id} - {signal_data['symbol']}")
            return signal_id
            
        except Exception as e:
            self.logger.error(f"Sinyal oluşturma hatası: {e}")
            return ""
            
    async def update_signal_prices(self):
        """Aktif sinyallerin fiyatlarını güncelle"""
        if not self.active_signals:
            return
            
        try:
            # Tüm aktif sinyallerin fiyatlarını kontrol et
            for signal_id, signal in list(self.active_signals.items()):
                try:
                    # Güncel fiyatı al
                    current_price = self.api.get_real_time_price(signal.symbol)
                    if current_price is None:
                        continue
                        
                    # Fiyatı güncelle
                    signal.current_price = current_price
                    signal.updated_at = datetime.now()
                    
                    # Kar/Zarar yüzdelerini hesapla
                    if signal.signal_type == "LONG":
                        profit_percentage = ((current_price - signal.entry_price) / signal.entry_price) * 100
                    else:  # SHORT
                        profit_percentage = ((signal.entry_price - current_price) / signal.entry_price) * 100
                        
                    # Max kar/zarar güncelle
                    if profit_percentage > signal.max_profit_percentage:
                        signal.max_profit_percentage = profit_percentage
                    elif profit_percentage < 0 and abs(profit_percentage) > signal.max_loss_percentage:
                        signal.max_loss_percentage = abs(profit_percentage)
                        
                    # TP ve SL kontrolü
                    await self._check_tp_sl_levels(signal)
                    
                    # Sinyal yaşı kontrolü
                    if self._is_signal_expired(signal):
                        await self._expire_signal(signal)
                        
                except Exception as e:
                    self.logger.error(f"Sinyal fiyat güncelleme hatası {signal_id}: {e}")
                    continue
                    
            # Güncellenmiş sinyalleri kaydet
            self._save_active_signals()
            
        except Exception as e:
            self.logger.error(f"Genel fiyat güncelleme hatası: {e}")
            
    async def _check_tp_sl_levels(self, signal: TrackedSignal):
        """TP ve SL seviyelerini kontrol et"""
        try:
            current_price = signal.current_price
            
            if signal.signal_type == "LONG":
                # LONG pozisyon kontrolleri
                
                # Stop Loss kontrolü
                if current_price <= signal.stop_loss and signal.status == SignalStatus.ACTIVE:
                    await self._hit_stop_loss(signal)
                    return
                    
                # TP kontrolleri
                if current_price >= signal.tp3 and 3 not in signal.hit_tp_levels:
                    await self._hit_take_profit(signal, 3)
                elif current_price >= signal.tp2 and 2 not in signal.hit_tp_levels:
                    await self._hit_take_profit(signal, 2)
                elif current_price >= signal.tp1 and 1 not in signal.hit_tp_levels:
                    await self._hit_take_profit(signal, 1)
                    
            else:  # SHORT pozisyon
                
                # Stop Loss kontrolü
                if current_price >= signal.stop_loss and signal.status == SignalStatus.ACTIVE:
                    await self._hit_stop_loss(signal)
                    return
                    
                # TP kontrolleri
                if current_price <= signal.tp3 and 3 not in signal.hit_tp_levels:
                    await self._hit_take_profit(signal, 3)
                elif current_price <= signal.tp2 and 2 not in signal.hit_tp_levels:
                    await self._hit_take_profit(signal, 2)
                elif current_price <= signal.tp1 and 1 not in signal.hit_tp_levels:
                    await self._hit_take_profit(signal, 1)
                    
        except Exception as e:
            self.logger.error(f"TP/SL kontrol hatası {signal.signal_id}: {e}")
            
    async def _hit_take_profit(self, signal: TrackedSignal, tp_level: int):
        """Take Profit seviyesi vurdu"""
        try:
            signal.hit_tp_levels.append(tp_level)
            signal.updated_at = datetime.now()
            
            # Status güncelle
            if tp_level == 1:
                signal.status = SignalStatus.TP1_HIT
            elif tp_level == 2:
                signal.status = SignalStatus.TP2_HIT
            elif tp_level == 3:
                signal.status = SignalStatus.TP3_HIT
                
            # Telegram bildirimi gönder
            notification_key = f"tp{tp_level}"
            if notification_key not in signal.notifications_sent:
                await self.telegram_bot.send_tp_update(
                    signal.signal_id, 
                    tp_level, 
                    signal.current_price, 
                    signal.symbol
                )
                signal.notifications_sent.append(notification_key)
                
            self.logger.info(f"TP{tp_level} vurdu: {signal.symbol} - {signal.current_price}")
            
            # TP3 vurduysa sinyali tamamla
            if tp_level == 3:
                await self._complete_signal(signal, "TP3 vurdu")
                
        except Exception as e:
            self.logger.error(f"TP hit işlemi hatası: {e}")
            
    async def _hit_stop_loss(self, signal: TrackedSignal):
        """Stop Loss vurdu"""
        try:
            signal.status = SignalStatus.STOP_LOSS
            signal.updated_at = datetime.now()
            
            # SL nedenini analiz et
            reason = await self._analyze_stop_loss_reason(signal)
            
            # Telegram bildirimi gönder
            if "stop_loss" not in signal.notifications_sent:
                await self.telegram_bot.send_sl_update(
                    signal.signal_id,
                    signal.current_price,
                    signal.symbol,
                    reason
                )
                signal.notifications_sent.append("stop_loss")
                
            self.logger.info(f"Stop Loss vurdu: {signal.symbol} - {signal.current_price}")
            
            # Sinyali tamamla
            await self._complete_signal(signal, f"Stop Loss - {reason}")
            
        except Exception as e:
            self.logger.error(f"Stop Loss işlemi hatası: {e}")
            
    async def _analyze_stop_loss_reason(self, signal: TrackedSignal) -> str:
        """Stop Loss nedenini analiz et"""
        try:
            # Basit neden analizi (geliştirilecek)
            loss_percentage = signal.max_loss_percentage
            
            if loss_percentage > 5:
                return "Güçlü tersine hareket"
            elif loss_percentage > 3:
                return "Trend değişimi"
            elif loss_percentage > 1:
                return "Düzeltme hareketi"
            else:
                return "Teknik seviye kırılması"
                
        except Exception as e:
            self.logger.error(f"SL neden analizi hatası: {e}")
            return "Belirsiz neden"
            
    async def _complete_signal(self, signal: TrackedSignal, completion_reason: str):
        """Sinyali tamamla"""
        try:
            # Sinyal sonucunu hazırla
            outcome = {
                'signal_id': signal.signal_id,
                'symbol': signal.symbol,
                'exit_price': signal.current_price,
                'exit_reason': completion_reason,
                'hit_tp_level': max(signal.hit_tp_levels) if signal.hit_tp_levels else 0,
                'max_drawdown': signal.max_loss_percentage,
                'duration_minutes': int((signal.updated_at - signal.created_at).total_seconds() / 60),
                'timestamp': signal.updated_at.isoformat()
            }
            
            # AI optimizer'a performans verisi gönder
            signal_dict = {
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profits': {
                    'tp1': signal.tp1,
                    'tp2': signal.tp2,
                    'tp3': signal.tp3
                },
                'confidence': 0.0,
                'analysis': signal.analysis_data
            }
            
            # Performance analizi artık yapılmıyor - direkt tamamla
            
            # Completed signals listesine ekle
            self.completed_signals.append(signal)
            
            # Active signals'den çıkar
            if signal.signal_id in self.active_signals:
                del self.active_signals[signal.signal_id]
                
            # Dosyaları güncelle
            self._save_active_signals()
            self._save_signal_history()
            
            self.logger.info(f"Sinyal tamamlandı: {signal.symbol} - {completion_reason}")
            
        except Exception as e:
            self.logger.error(f"Sinyal tamamlama hatası: {e}")
            
    async def _expire_signal(self, signal: TrackedSignal):
        """Süresi dolmuş sinyali sonlandır"""
        try:
            signal.status = SignalStatus.EXPIRED
            await self._complete_signal(signal, "Süre doldu")
            
        except Exception as e:
            self.logger.error(f"Sinyal süre dolma hatası: {e}")
            
    def _is_signal_expired(self, signal: TrackedSignal) -> bool:
        """Sinyalin süresi dolmuş mu kontrol et"""
        age_hours = (datetime.now() - signal.created_at).total_seconds() / 3600
        return age_hours > self.max_signal_age_hours
        
    def get_active_signals_summary(self) -> Dict:
        """Aktif sinyallerin özeti"""
        try:
            summary = {
                'total_active': len(self.active_signals),
                'by_status': {},
                'by_symbol': {},
                'performance_summary': {
                    'profitable_signals': 0,
                    'losing_signals': 0,
                    'tp1_hits': 0,
                    'tp2_hits': 0,
                    'tp3_hits': 0
                }
            }
            
            for signal in self.active_signals.values():
                # Status'a göre gruppla
                status_key = signal.status.value
                summary['by_status'][status_key] = summary['by_status'].get(status_key, 0) + 1
                
                # Symbol'e göre gruppla
                summary['by_symbol'][signal.symbol] = summary['by_symbol'].get(signal.symbol, 0) + 1
                
                # Performans hesapla
                if signal.max_profit_percentage > 0:
                    summary['performance_summary']['profitable_signals'] += 1
                if signal.max_loss_percentage > 0:
                    summary['performance_summary']['losing_signals'] += 1
                    
                # TP hits
                for tp_level in signal.hit_tp_levels:
                    summary['performance_summary'][f'tp{tp_level}_hits'] += 1
                    
            return summary
            
        except Exception as e:
            self.logger.error(f"Özet hazırlama hatası: {e}")
            return {}
            
    def _save_active_signals(self):
        """Aktif sinyalleri kaydet"""
        try:
            signals_data = {}
            for signal_id, signal in self.active_signals.items():
                signal_dict = asdict(signal)
                # Datetime objelerini string'e çevir
                signal_dict['created_at'] = signal.created_at.isoformat()
                signal_dict['updated_at'] = signal.updated_at.isoformat()
                signal_dict['status'] = signal.status.value
                signals_data[signal_id] = signal_dict
                
            with open(self.active_signals_file, 'w', encoding='utf-8') as f:
                json.dump(signals_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Aktif sinyal kaydetme hatası: {e}")
            
    def _save_signal_history(self):
        """Sinyal geçmişini kaydet"""
        try:
            history_data = []
            for signal in self.completed_signals:
                signal_dict = asdict(signal)
                signal_dict['created_at'] = signal.created_at.isoformat()
                signal_dict['updated_at'] = signal.updated_at.isoformat()
                signal_dict['status'] = signal.status.value
                history_data.append(signal_dict)
                
            with open(self.signal_history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Sinyal geçmişi kaydetme hatası: {e}")
            
    def load_signals(self):
        """Kayıtlı sinyalleri yükle"""
        try:
            # Aktif sinyalleri yükle
            try:
                with open(self.active_signals_file, 'r', encoding='utf-8') as f:
                    signals_data = json.load(f)
                    
                for signal_id, signal_dict in signals_data.items():
                    signal_dict['created_at'] = datetime.fromisoformat(signal_dict['created_at'])
                    signal_dict['updated_at'] = datetime.fromisoformat(signal_dict['updated_at'])
                    signal_dict['status'] = SignalStatus(signal_dict['status'])
                    
                    signal = TrackedSignal(**signal_dict)
                    self.active_signals[signal_id] = signal
                    
                self.logger.info(f"{len(self.active_signals)} aktif sinyal yüklendi")
                
            except FileNotFoundError:
                self.logger.info("Aktif sinyal dosyası bulunamadı")
                
            # Sinyal geçmişini yükle
            try:
                with open(self.signal_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    
                for signal_dict in history_data:
                    signal_dict['created_at'] = datetime.fromisoformat(signal_dict['created_at'])
                    signal_dict['updated_at'] = datetime.fromisoformat(signal_dict['updated_at'])
                    signal_dict['status'] = SignalStatus(signal_dict['status'])
                    
                    signal = TrackedSignal(**signal_dict)
                    self.completed_signals.append(signal)
                    
                self.logger.info(f"{len(self.completed_signals)} tamamlanmış sinyal yüklendi")
                
            except FileNotFoundError:
                self.logger.info("Sinyal geçmişi dosyası bulunamadı")
                
        except Exception as e:
            self.logger.error(f"Sinyal yükleme hatası: {e}")
            
    async def start_tracking(self):
        """Sinyal takibini başlat"""
        self.logger.info("Sinyal takibi başlatıldı")
        
        while True:
            try:
                await self.update_signal_prices()
                await asyncio.sleep(self.price_check_interval)
                
            except Exception as e:
                self.logger.error(f"Tracking loop hatası: {e}")
                await asyncio.sleep(60)  # Hata durumunda 1 dakika bekle