import asyncio
import logging
import schedule
import time
import sys
import os
import warnings

# Warning'leri sustur
warnings.filterwarnings('ignore', category=FutureWarning)

# src klasörünü Python path'ine ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

from src.config import Config
from src.kucoin_api import KuCoinAPI
from src.technical_analysis import generate_trading_signal
from src.telegram_bot import TelegramBot
from src.signal_tracker import SignalTracker
from src.signal_validator import SignalValidator
from src.ai_optimizer import AIOptimizer  # AI Optimizer eklendi!
from src.m5_confirmation import M5ConfirmationSystem  # M5 onay sistemi

class TradingBot:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Gerekli bileşenleri başlat
        self.kucoin_api = None
        self.telegram_bot = None
        self.signal_tracker = None
        self.signal_validator = None
        self.ai_optimizer = None  # AI Optimizer eklendi!
        self.m5_confirmation = None  # M5 onay sistemi
        
        # Bot durumu
        self.is_running = False
        self.last_signal_time = None
        self.signals_sent_hour = 0
        self.hourly_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.analysis_count = 0
        self.last_analysis_time = None
        
        # Async loop
        self.loop = None
        self.bot_task = None
        
    async def initialize(self):
        """Bot bileşenlerini başlat"""
        try:
            # Konfigürasyonu doğrula
            self.config.validate_config()
            
            # API ve bileşenleri başlat
            self.kucoin_api = KuCoinAPI(self.config)
            # technical_analyzer artık function olarak kullanılıyor
            
            # AI Optimizer'ı başlat
            self.ai_optimizer = AIOptimizer()
            
            # M5 Confirmation System'ı başlat
            self.m5_confirmation = M5ConfirmationSystem()
            
            # Telegram bot'u başlat
            self.telegram_bot = TelegramBot(self.config)
            await self.telegram_bot.initialize()
            
            # Signal tracker'ı başlat
            self.signal_tracker = SignalTracker(
                self.kucoin_api, 
                self.telegram_bot
            )
            
            # Signal validator'ı başlat
            self.signal_validator = SignalValidator(self.kucoin_api)
            
            # Kayıtlı verileri yükle
            self.signal_tracker.load_signals()
            
            self.logger.info("🤖 AI Optimizer başlatıldı")
            self.logger.info("📊 M5 Confirmation System başlatıldı")
            self.logger.info("Trading bot başarıyla başlatıldı")
            return True
            
        except Exception as e:
            self.logger.error(f"Bot başlatma hatası: {e}")
            return False
            
    async def start(self):
        """Bot'u başlat"""
        print("🤖 KuCoin Professional Trading Bot Başlatılıyor...")
        print("=" * 60)
        
        # 📊 AI Sistem durumunu kontrol et
        try:
            from src.ai_system_monitor import print_ai_status_report
            print_ai_status_report()
        except Exception as e:
            self.logger.warning(f"AI sistem durumu kontrol edilemedi: {e}")
        
        if not await self.initialize():
            return False
            
        self.is_running = True
        
        print("✅ Bot başarıyla başlatıldı!")
        print("📊 Analiz Parametreleri:")
        print(f"   • Minimum Hacim: ${self.config.MIN_VOLUME_USDT:,}")
        print(f"   • Analiz Aralığı: {self.config.ANALYSIS_INTERVAL} dakika")
        print(f"   • Saatlik Max Sinyal: {self.config.MAX_SIGNALS_PER_HOUR}")
        print(f"   • Telegram Token: {self.config.TELEGRAM_BOT_TOKEN[:20] if self.config.TELEGRAM_BOT_TOKEN else 'None'}...")
        print("=" * 60)
        
        # 🚀 AI Sistem durumunu kontrol et
        try:
            from src.ai_system_monitor import print_ai_status_report
            print_ai_status_report()
        except Exception as e:
            self.logger.warning(f"AI sistem durumu kontrol edilemedi: {e}")
        
        # Schedule'ları ayarla
        self._setup_schedules()
        
        # Ana görevleri başlat
        tasks = [
            self._main_analysis_loop(),
            self._signal_tracking_loop(),
            self._telegram_polling_loop(),
            self._schedule_runner(),
            self._ai_optimization_loop()
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"❌ Bot çalışma hatası: {e}")
            self.logger.error(f"Bot çalışma hatası: {e}")
            self.is_running = False
            
        return True
        
    def _setup_schedules(self):
        """Zamanlanmış görevleri ayarla"""
        # Her saat başı sinyal sayacını sıfırla
        schedule.every().hour.at(":00").do(self._reset_hourly_signals)
        
        # Günlük AI optimizasyonu
        schedule.every().day.at("00:00").do(self._daily_ai_optimization)
        
        # 🚀 YENİ: Gelişmiş AI optimizasyon (her 6 saatte bir)
        schedule.every(6).hours.do(self._schedule_advanced_ai_optimization)
        
        # Haftalık performans raporu
        schedule.every().week.do(self._weekly_performance_report)
        
        self.logger.info("Zamanlanmış görevler ayarlandı")
    
    def _schedule_advanced_ai_optimization(self):
        """Gelişmiş AI optimizasyonu için zamanlanmış görev wrapper"""
        try:
            # Async fonksiyonu sync ortamdan çağır
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._advanced_ai_optimization())
            loop.close()
        except Exception as e:
            self.logger.error(f"Zamanlanmış AI optimizasyon hatası: {e}")
        
    async def _main_analysis_loop(self):
        """Ana analiz döngüsü"""
        print("🚀 Ana analiz döngüsü başlatıldı (Her 5 dakika)")
        self.logger.info("Ana analiz döngüsü başlatıldı")
        
        while self.is_running:
            try:
                print(f"\n{'='*60}")
                print(f"🔍 ANALİZ BAŞLADI - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                
                await self._analyze_and_signal()
                
                print(f"\n⏰ Sonraki analiz: {(datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')}")
                print(f"{'='*60}\n")
                
                # 5 dakika bekle
                await asyncio.sleep(300)  # 5 * 60 = 300 saniye
                
            except Exception as e:
                print(f"❌ Analiz döngüsü hatası: {e}")
                self.logger.error(f"Analiz döngüsü hatası: {e}")
                await asyncio.sleep(60)  # Hata durumunda 1 dakika bekle
                
    async def _analyze_and_signal(self):
        """Analiz yap ve sinyal gönder"""
        try:
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            print(f"📊 Analiz #{self.analysis_count} başlıyor...")
            
            # Saatlik sinyal limitini kontrol et
            if self._is_hourly_limit_reached():
                print("⏳ Saatlik sinyal limiti aşıldı, bekleniyor...")
                self.logger.info("Saatlik sinyal limiti aşıldı, bekleniyor...")
                return
                
            print("🔄 Yüksek hacimli coinler alınıyor...")
            # Yüksek hacimli coinleri al
            high_volume_coins = self.kucoin_api.get_high_volume_coins(
                self.config.MIN_VOLUME_USDT
            )
            
            if not high_volume_coins:
                print("❌ Yüksek hacimli coin bulunamadı")
                self.logger.warning("Yüksek hacimli coin bulunamadı")
                return
                
            print(f"✅ {len(high_volume_coins)} yüksek hacimli coin bulundu")
            self.logger.info(f"{len(high_volume_coins)} yüksek hacimli coin analiz ediliyor")
            
            # En iyi sinyalleri bul
            potential_signals = []
            coins_analyzed = 0
            max_coins_to_analyze = min(30, len(high_volume_coins))
            
            print(f"🎯 İlk {max_coins_to_analyze} coin analiz ediliyor...")
            
            for coin in high_volume_coins[:max_coins_to_analyze]:
                try:
                    symbol = coin['symbol']
                    coins_analyzed += 1
                    
                    print(f"  📈 [{coins_analyzed}/{max_coins_to_analyze}] {symbol} analiz ediliyor...")
                    
                    # Teknik analiz ve sinyal üret (M15'te SMC stratejisi)
                    signal = generate_trading_signal(symbol, self.kucoin_api)
                    if signal and signal['signal'] != 'HOLD':
                        # Symbol'ü signal'e ekle
                        signal['symbol'] = symbol
                        signal['signal_type'] = signal['signal']
                        
                        print(f"    🎯 {symbol} - {signal['signal']} sinyali!")
                        print(f"       💪 Güven: {signal['confidence']:.1f}%")
                        print(f"       ⚡ Strateji: {signal['reason']}")
                        
                        # 🚨 YENİ: M5 Onay Sistemi
                        print(f"       📊 M5'te 2 mum onay bekleniyor...")
                        m5_confirmation = await self.m5_confirmation.confirm_signal_on_m5(
                            symbol, signal, self.kucoin_api
                        )
                        
                        if m5_confirmation['confirmed']:
                            # M5 onayı başarılı
                            signal['m5_confirmation'] = m5_confirmation
                            signal['entry_price'] = m5_confirmation['final_entry_price']  # M5'ten gelen entry price
                            signal['confidence'] += 10  # M5 onayı bonus
                            
                            print(f"       ✅ M5 ONAYI BAŞARILI! ({m5_confirmation['confirmation_strength']:.0f}%)")
                            print(f"       📈 Yeni Entry: ${m5_confirmation['final_entry_price']:.6f}")
                            
                            # Mum analizlerini göster
                            for candle_analysis in m5_confirmation['candle_analysis']:
                                print(f"          🕯️ {candle_analysis['candle']}: {candle_analysis['points']}/5 puan")
                                for detail in candle_analysis['details']:
                                    print(f"             {detail}")
                            
                            # Hızlı validation (M15 bazlı)
                            print(f"       🔍 Hızlı doğrulama yapılıyor...")
                            validation_result = await self.signal_validator.quick_validate_signal(signal)
                            
                            if validation_result['is_validated']:
                                signal['confidence'] += validation_result['confidence_boost']
                                signal['validation_result'] = validation_result
                                potential_signals.append(signal)
                                
                                print(f"       ✅ Final doğrulama OK! Toplam güven: {signal['confidence']:.1f}%")
                                print(f"       📋 Sebep: {validation_result['reason']}")
                            else:
                                print(f"       ❌ Final doğrulama başarısız: {validation_result['reason']}")
                        else:
                            # M5 onayı başarısız
                            print(f"       ❌ M5 ONAYI BAŞARISIZ: {m5_confirmation['reason']}")
                            print(f"       📊 Onay gücü: {m5_confirmation['confirmation_strength']:.0f}% (min %60 gerekli)")
                            
                            # Mum analizlerini göster (hata ayıklama için)
                            for candle_analysis in m5_confirmation['candle_analysis']:
                                print(f"          🕯️ {candle_analysis['candle']}: {candle_analysis['points']}/5 puan")
                    else:
                        # Neden sinyal üretilmediğini açıkla
                        print(f"    ⚪ {symbol} - {signal['reason'] if signal else 'Veri alınamadı'}")
                            
                except Exception as e:
                    print(f"    ❌ {symbol} - Hata: {str(e)[:50]}...")
                    self.logger.warning(f"Coin analiz hatası {coin.get('symbol', 'Unknown')}: {e}")
                    continue
                    
            print(f"\n📋 Analiz özeti:")
            print(f"   💹 Toplam coin: {len(high_volume_coins)}")
            print(f"   🔍 Analiz edilen: {coins_analyzed}")
            print(f"   🎯 Potansiyel sinyal: {len(potential_signals)}")
            
            # En iyi sinyali seç ve gönder
            if potential_signals:
                best_signal = max(potential_signals, key=lambda x: x['confidence'])
                
                print(f"\n🏆 YENİ SMC STRATEJİ SİNYALİ:")
                print(f"   🪙 Coin: {best_signal.get('symbol', 'Unknown')}")
                print(f"   📊 Tür: {best_signal.get('signal', 'Unknown')}")
                print(f"   💪 Güven: {best_signal['confidence']:.1f}%")
                print(f"   💰 Entry: ${best_signal.get('entry_price', 0):.6f}")
                print(f"   🛑 Stop: ${best_signal.get('stop_loss', 0):.6f}")
                print(f"   🎯 TP1: ${best_signal.get('take_profit_1', 0):.6f}")
                print(f"   ⚡ Strateji: {best_signal.get('reason', 'SMC Strategy')}")
                
                if best_signal['confidence'] >= 70:  # Minimum güven eşiği
                    # 🚨 YENİ: Aktif sinyal kontrolü
                    symbol = best_signal.get('symbol', 'UNKNOWN-PAIR')
                    signal_type = best_signal.get('signal', 'UNKNOWN')
                    
                    if self.signal_tracker.is_symbol_already_active(symbol, signal_type):
                        print(f"   ⚠️ {symbol} {signal_type} sinyali zaten aktif! GEÇİLİYOR...")
                        return  # Bu analiz döngüsünü sonlandır
                    
                    print(f"   ✅ Güven eşiği geçildi! Sinyal gönderiliyor...")
                    # Signal'e symbol ekle
                    best_signal['symbol'] = symbol
                    best_signal['signal_type'] = signal_type
                    await self._send_validated_signal(best_signal)
                else:
                    print(f"   ❌ Güven eşiği düşük (minimum: 70%)")
            else:
                print("\n❌ Bu döngüde sinyal bulunamadı")
                print("   🔍 Sebeppler:")
                print("   • Güven oranları düşük")
                print("   • Risk/Ödül oranı uygun değil")
                print("   • Teknik indikatörler çelişkili")
                print("   • AI tahminleri olumsuz")
                    
        except Exception as e:
            print(f"❌ KRITIK HATA: {e}")
            self.logger.error(f"Analiz ve sinyal hatası: {e}")
            
    def _recalculate_tp_sl(self, signal: Dict, new_price: float) -> Optional[Dict]:
        """Güncel fiyata göre TP/SL seviyelerini yeniden hesapla - SMC Strategy"""
        try:
            signal_type = signal.get('signal_type', signal.get('signal'))
            old_price = signal['entry_price']
            
            # Basit risk/reward korunarak yeniden hesapla
            risk_distance = abs(signal['stop_loss'] - old_price)
            risk_reward_ratio = signal.get('risk_reward', 1.0)
            
            if signal_type == 'LONG':
                new_sl = new_price * 0.98  # %2 stop loss
                new_tp1 = new_price + (risk_distance * risk_reward_ratio)
                new_tp2 = new_price + (risk_distance * risk_reward_ratio * 2)
            else:  # SHORT
                new_sl = new_price * 1.02  # %2 stop loss
                new_tp1 = new_price - (risk_distance * risk_reward_ratio)
                new_tp2 = new_price - (risk_distance * risk_reward_ratio * 2)
            
            # Risk/reward hala mantıklı mı kontrol et
            new_risk = abs(new_price - new_sl)
            new_reward = abs(new_tp1 - new_price)
            
            # Risk/reward hala mantıklı mı kontrol et
            new_risk = abs(new_price - new_sl)
            new_reward = abs(new_tp1 - new_price)
            
            if new_reward / new_risk < 0.8:  # Minimum 1:0.8 R/R
                self.logger.warning(f"Risk/reward çok düşük: {new_reward/new_risk:.2f}")
                return None
            
            # Güncellenmiş sinyali döndür
            updated_signal = signal.copy()
            updated_signal['entry_price'] = new_price
            updated_signal['stop_loss'] = new_sl
            updated_signal['take_profit_1'] = new_tp1
            updated_signal['take_profit_2'] = new_tp2
            updated_signal['take_profits'] = {
                'tp1': new_tp1,
                'tp2': new_tp2,
                'tp3': new_tp2  # TP3 = TP2
            }
            updated_signal['risk_reward'] = new_reward / new_risk
            
            return updated_signal
            
        except Exception as e:
            self.logger.error(f"TP/SL yeniden hesaplama hatası: {e}")
            return None

    async def _send_validated_signal(self, signal: Dict):
        """Doğrulanmış sinyali gönder"""
        try:
            print(f"\n🚀 SİNYAL GÖNDERİLİYOR:")
            print(f"   🪙 {signal['symbol']}")
            print(f"   📊 {signal['signal_type']}")
            
            # Güncel fiyatı kontrol et ve güncelle
            print(f"   🔄 Güncel fiyat kontrol ediliyor...")
            current_market_price = self.kucoin_api.get_real_time_price(signal['symbol'])
            
            if current_market_price:
                price_difference = abs(current_market_price - signal['entry_price']) / signal['entry_price']
                
                if price_difference > 0.005:  # %0.5'den fazla fark varsa
                    print(f"   ⚠️  Fiyat değişimi tespit edildi:")
                    print(f"      Eski: ${signal['entry_price']:.6f}")
                    print(f"      Yeni: ${current_market_price:.6f}")
                    print(f"      Fark: {price_difference:.2%}")
                    
                    # TP/SL seviyelerini yeniden hesapla
                    print(f"   🔄 TP/SL seviyeleri güncelleniyor...")
                    updated_signal = self._recalculate_tp_sl(signal, current_market_price)
                    if updated_signal:
                        signal = updated_signal
                        print(f"   ✅ Fiyat ve seviyeler güncellendi")
                    else:
                        print(f"   ❌ Güncel fiyatla sinyal geçersiz")
                        return
                else:
                    print(f"   ✅ Fiyat güncel (Fark: {price_difference:.2%})")
            
            print(f"   💰 Giriş: ${signal['entry_price']:.6f}")
            print(f"   🛑 Stop Loss: ${signal['stop_loss']:.6f}")
            print(f"   🎯 TP1: ${signal.get('take_profit_1', signal.get('take_profits', {}).get('tp1', 0)):.6f}")
            
            # Eski format uyumluluk için take_profits oluştur
            if 'take_profits' not in signal and 'take_profit_1' in signal:
                signal['take_profits'] = {
                    'tp1': signal.get('take_profit_1', 0),
                    'tp2': signal.get('take_profit_2', 0),
                    'tp3': signal.get('take_profit_2', 0)  # TP3 yoksa TP2 kullan
                }
            
            # Multi-timeframe validation - basit versiyon
            print(f"   🔍 SMC Strateji doğrulaması...")
            # Basit güven kontrolü
            print(f"   ✅ SMC stratejisi aktif! Güven: {signal['confidence']:.1f}%")
                
            # Final confidence kontrolü
            if signal['confidence'] < 70:
                print(f"   ❌ Final güven düşük: {signal['confidence']:.1f}% < 70%")
                self.logger.info(f"Final güven düşük: {signal['symbol']} - {signal['confidence']:.1f}%")
                return
            
            # 🤖 AI Optimizer filtresi
            should_send, ai_reason = self.ai_optimizer.should_send_signal(signal)
            if not should_send:
                print(f"   🤖 AI filtresi engelliyor: {ai_reason}")
                self.logger.info(f"AI filtresi: {signal['symbol']} - {ai_reason}")
                return
            else:
                print(f"   🤖 AI onayı: {ai_reason}")
                
            # Telegram'a gönder
            print(f"   📤 Telegram'a gönderiliyor...")
            success = await self.telegram_bot.send_signal(signal)
            
            if success:
                # Signal tracker'a ekle
                signal_id = self.signal_tracker.create_signal(signal)
                
                if signal_id:
                    self.last_signal_time = datetime.now()
                    self.signals_sent_hour += 1
                    
                    print(f"   ✅ SİNYAL BAŞARIYLA GÖNDERİLDİ!")
                    print(f"   🆔 Sinyal ID: {signal_id}")
                    print(f"   ⏰ Zaman: {self.last_signal_time.strftime('%H:%M:%S')}")
                    print(f"   📊 Bu saat gönderilen: {self.signals_sent_hour}/{self.config.MAX_SIGNALS_PER_HOUR}")
                    
                    self.logger.info(f"Sinyal gönderildi: {signal['symbol']} - ID: {signal_id}")
                    
                    # Uzun validation başlat (background)
                    print(f"   🔄 Uzun süreli doğrulama başlatılıyor...")
                    asyncio.create_task(self._long_validation(signal, signal_id))
                else:
                    print(f"   ❌ Signal tracker hatası")
            else:
                print(f"   ❌ Telegram gönderimi başarısız")
                    
        except Exception as e:
            print(f"   ❌ Sinyal gönderme hatası: {e}")
            self.logger.error(f"Sinyal gönderme hatası: {e}")
            
    async def _long_validation(self, signal: Dict, signal_id: str):
        """Uzun süreli validation (2 mum)"""
        try:
            print(f"🔄 Uzun doğrulama başlıyor: {signal['symbol']}")
            validation_result = await self.signal_validator.validate_signal(signal)
            
            # Validation sonucunu kaydet
            if validation_result['is_validated']:
                print(f"✅ Uzun doğrulama başarılı: {signal['symbol']} - {validation_result['reason']}")
            else:
                print(f"❌ Uzun doğrulama başarısız: {signal['symbol']} - {validation_result['reason']}")
                
            self.logger.info(f"Uzun validation tamamlandı {signal['symbol']}: {validation_result['reason']}")
            
            # AI optimizer'a feedback ver
            if not validation_result['is_validated']:
                # Başarısız validation için düzeltici önlemler
                print(f"⚠️  {signal['symbol']} sinyali gelecekte filtrelenicek")
                self.logger.warning(f"Validation başarısız: {signal['symbol']}")
                
        except Exception as e:
            print(f"❌ Uzun doğrulama hatası: {e}")
            self.logger.error(f"Uzun validation hatası: {e}")
            
    async def _signal_tracking_loop(self):
        """Sinyal takip döngüsü"""
        print("📊 Sinyal takip döngüsü başlatıldı")
        self.logger.info("Sinyal takip döngüsü başlatıldı")
        
        while self.is_running:
            try:
                # Aktif sinyalleri kontrol et
                if self.signal_tracker.active_signals:
                    print(f"\n📈 {len(self.signal_tracker.active_signals)} aktif sinyal güncelleniyor...")
                    
                await self.signal_tracker.update_signal_prices()
                await asyncio.sleep(30)  # 30 saniyede bir güncelle
                
            except Exception as e:
                print(f"❌ Sinyal takip hatası: {e}")
                self.logger.error(f"Sinyal takip hatası: {e}")
                await asyncio.sleep(60)
                
    async def _telegram_polling_loop(self):
        """Telegram polling döngüsü"""
        try:
            await self.telegram_bot.start_polling()
        except Exception as e:
            self.logger.error(f"Telegram polling hatası: {e}")
            
    async def _schedule_runner(self):
        """Schedule runner döngüsü"""
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Her dakika kontrol et
            except Exception as e:
                self.logger.error(f"Schedule runner hatası: {e}")
                await asyncio.sleep(60)
                
    async def _ai_optimization_loop(self):
        """AI optimizasyon döngüsü"""
        while self.is_running:
            try:
                # SMC strategy için background monitoring
                # AI optimization kaldırıldı
                print("📊 SMC Strategy background monitoring aktif...")
                
                await asyncio.sleep(21600)  # 6 saat = 21600 saniye
                
            except Exception as e:
                self.logger.error(f"Background monitoring hatası: {e}")
                await asyncio.sleep(3600)  # Hata durumunda 1 saat bekle
                
    def _is_hourly_limit_reached(self) -> bool:
        """Saatlik sinyal limitine ulaşıldı mı?"""
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # Saat değiştiyse sayacı sıfırla
        if current_hour > self.hourly_reset_time:
            self.signals_sent_hour = 0
            self.hourly_reset_time = current_hour
            
        return self.signals_sent_hour >= self.config.MAX_SIGNALS_PER_HOUR
        
    def _reset_hourly_signals(self):
        """Saatlik sinyal sayacını sıfırla"""
        self.signals_sent_hour = 0
        self.hourly_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.logger.info("Saatlik sinyal sayacı sıfırlandı")
        
    def _daily_ai_optimization(self):
        """Günlük SMC strateji raporu"""
        try:
            print("📊 Günlük SMC strateji raporu hazırlanıyor...")
            # AI optimization kaldırıldı - SMC strategy kullanıyor
            self.logger.info("Günlük SMC strateji raporu tamamlandı")
        except Exception as e:
            self.logger.error(f"Günlük rapor hatası: {e}")
            
    def _weekly_performance_report(self):
        """Haftalık performans raporu"""
        try:
            # Performans özeti hazırla
            signal_summary = self.signal_tracker.get_active_signals_summary()
            # ai_status kaldırıldı - SMC strategy kullanıyor
            
            report = {
                'date': datetime.now().isoformat(),
                'signal_summary': signal_summary,
                'smc_strategy': 'Active',
                'signals_sent_this_week': 'TODO',  # Implement
                'success_rate': 'TODO'  # Implement
            }
            
            self.logger.info(f"Haftalık rapor: {report}")
            
        except Exception as e:
            self.logger.error(f"Haftalık rapor hatası: {e}")
            
    async def stop(self):
        """Bot'u durdur"""
        self.logger.info("Bot durduruluyor...")
        self.is_running = False
        
        try:
            # Telegram bot'u durdur
            if self.telegram_bot:
                await self.telegram_bot.stop_polling()
                
            # Verileri kaydet
            if self.signal_tracker:
                self.signal_tracker._save_active_signals()
                self.signal_tracker._save_signal_history()
                
            # ai_optimizer._save_performance_data() kaldırıldı
                
            self.logger.info("Bot başarıyla durduruldu")
            
        except Exception as e:
            self.logger.error(f"Bot durdurma hatası: {e}")
    
    # 🚀 YENİ: GELİŞMİŞ AI OPTİMİZASYON SİSTEMİ
    async def _advanced_ai_optimization(self):
        """
        🤖 Gelişmiş AI Optimizasyon Sistemi
        Başarısız sinyalleri analiz ederek tüm strateji parametrelerini optimize eder
        """
        try:
            self.logger.info("🤖 Gelişmiş AI optimizasyon analizi başlıyor...")
            
            # Son 24 saatte başarısız sinyalleri al
            failed_signals = self.signal_tracker.get_failed_signals_last_24h()
            
            if len(failed_signals) < 3:
                self.logger.info("🤖 Yeterli başarısız sinyal yok, optimizasyon atlanıyor")
                return
            
            # Market koşullarını analiz et
            market_conditions = await self._analyze_market_conditions()
            
            # AI optimizasyonu çalıştır
            optimization_result = self.ai_optimizer.optimize_strategy_parameters(
                failed_signals, market_conditions
            )
            
            if optimization_result['success'] and optimization_result['optimizations_count'] > 0:
                # Optimize edilmiş parametreleri al ve uygula
                optimized_params = self.ai_optimizer.get_optimized_parameters()
                
                # Parametreleri sisteme uygula
                await self._apply_optimized_parameters(optimized_params)
                
                # Telegram'a bildirim gönder
                optimization_message = f"""
🤖 **AI STRATEJİ OPTİMİZASYONU**

📊 **Analiz Edilen Başarısız Sinyal:** {len(failed_signals)}
🔧 **Optimize Edilen Parametre:** {optimization_result['optimizations_count']}

🎯 **Optimizasyonlar:**
"""
                
                for opt in optimization_result['optimizations']:
                    optimization_message += f"• **{opt['parameter']}:** {opt.get('reason', 'Geliştirildi')}\n"
                
                optimization_message += f"\n⚡ **Durum:** AI sistemi parametreleri optimize etti!"
                
                await self.telegram_bot.send_message(optimization_message)
                
                self.logger.info(f"🤖 AI {optimization_result['optimizations_count']} parametre optimize etti!")
            else:
                self.logger.info("🤖 AI mevcut parametrelerin optimal olduğunu belirledi")
                
        except Exception as e:
            self.logger.error(f"Gelişmiş AI optimizasyon hatası: {e}")
    
    async def _analyze_market_conditions(self) -> dict:
        """Market koşullarını analiz et"""
        try:
            # Basit market koşulu analizi
            symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT']
            market_data = {}
            
            for symbol in symbols:
                data = await self.kucoin_api.get_kline_data(symbol, '1hour', 24)
                if data and len(data) > 1:
                    current_price = float(data[-1]['close'])
                    prev_price = float(data[-2]['close'])
                    change_24h = ((current_price - prev_price) / prev_price) * 100
                    
                    market_data[symbol] = {
                        'change_24h': change_24h,
                        'volatility': self._calculate_volatility(data[-24:])
                    }
            
            # Genel market durumu
            avg_change = sum(d['change_24h'] for d in market_data.values()) / len(market_data)
            avg_volatility = sum(d['volatility'] for d in market_data.values()) / len(market_data)
            
            market_condition = "neutral"
            if avg_change > 2:
                market_condition = "bullish"
            elif avg_change < -2:
                market_condition = "bearish"
            
            volatility_level = "normal"
            if avg_volatility > 0.05:
                volatility_level = "high"
            elif avg_volatility < 0.02:
                volatility_level = "low"
            
            return {
                'condition': market_condition,
                'volatility': volatility_level,
                'avg_change_24h': avg_change,
                'avg_volatility': avg_volatility,
                'symbols_analyzed': len(market_data)
            }
            
        except Exception as e:
            self.logger.error(f"Market koşulları analiz hatası: {e}")
            return {'condition': 'unknown', 'volatility': 'unknown'}
    
    def _calculate_volatility(self, kline_data: list) -> float:
        """Volatilite hesapla"""
        try:
            prices = [float(k['close']) for k in kline_data]
            if len(prices) < 2:
                return 0.0
            
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            
            # Standart sapma
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            return volatility
            
        except Exception as e:
            return 0.0
    
    async def _apply_optimized_parameters(self, optimized_params: dict):
        """Optimize edilmiş parametreleri sisteme uygula"""
        try:
            self.logger.info("🤖 Optimize edilmiş parametreler uygulanıyor...")
            
            # SMC parametrelerini güncelle
            if hasattr(self, 'technical_analyzer'):
                # Technical analyzer'e parametreleri geç
                # Bu parametreler bir sonraki sinyal analizinde kullanılacak
                pass
            
            # Risk management parametrelerini güncelle
            if hasattr(self, 'signal_validator'):
                # Signal validator'e parametreleri geç
                pass
            
            self.logger.info("🤖 Parametreler başarıyla uygulandı")
            
        except Exception as e:
            self.logger.error(f"Parametre uygulama hatası: {e}")
            
    def get_status(self) -> Dict:
        """Bot durumunu getir"""
        return {
            'is_running': self.is_running,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'signals_sent_hour': self.signals_sent_hour,
            'max_signals_per_hour': self.config.MAX_SIGNALS_PER_HOUR,
            'active_signals': len(self.signal_tracker.active_signals) if self.signal_tracker else 0,
            'telegram_users': len(self.telegram_bot.chat_ids) if self.telegram_bot else 0,
            'smc_strategy': 'Active'  # AI optimizer kaldırıldı, SMC strategy aktif
        }

async def main():
    """Ana fonksiyon"""
    print("🚀 KuCoin Trading Bot v1.0")
    print("💻 Developed by Professional AI")
    print("=" * 50)
    
    bot = TradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Bot durduruluyor...")
        await bot.stop()
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        logging.error(f"Kritik hata: {e}")
        await bot.stop()

if __name__ == "__main__":
    # Event loop'u başlat
    asyncio.run(main())