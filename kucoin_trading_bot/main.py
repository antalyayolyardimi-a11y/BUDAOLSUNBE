import asyncio
import logging
import schedule
import time
import sys
import os

# src klasörünü Python path'ine ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from typing import Dict, List
import threading

from config import Config
from kucoin_api import KuCoinAPI
from technical_analysis import TechnicalAnalyzer
from telegram_bot import TelegramBot
from signal_tracker import SignalTracker
from signal_validator import SignalValidator
from ai_optimizer import AIOptimizer

class TradingBot:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Gerekli bileşenleri başlat
        self.kucoin_api = None
        self.technical_analyzer = None
        self.telegram_bot = None
        self.signal_tracker = None
        self.signal_validator = None
        self.ai_optimizer = None
        
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
            self.technical_analyzer = TechnicalAnalyzer(self.kucoin_api)
            self.ai_optimizer = AIOptimizer()
            
            # Telegram bot'u başlat
            self.telegram_bot = TelegramBot(self.config)
            await self.telegram_bot.initialize()
            
            # Signal tracker'ı başlat
            self.signal_tracker = SignalTracker(
                self.kucoin_api, 
                self.telegram_bot, 
                self.ai_optimizer
            )
            
            # Signal validator'ı başlat
            self.signal_validator = SignalValidator(self.kucoin_api)
            
            # Kayıtlı verileri yükle
            self.signal_tracker.load_signals()
            self.ai_optimizer.load_performance_data()
            
            self.logger.info("Trading bot başarıyla başlatıldı")
            return True
            
        except Exception as e:
            self.logger.error(f"Bot başlatma hatası: {e}")
            return False
            
    async def start(self):
        """Bot'u başlat"""
        print("🤖 KuCoin Professional Trading Bot Başlatılıyor...")
        print("=" * 60)
        
        if not await self.initialize():
            return False
            
        self.is_running = True
        
        print("✅ Bot başarıyla başlatıldı!")
        print("📊 Analiz Parametreleri:")
        print(f"   • Minimum Hacim: ${self.config.MIN_VOLUME_USDT:,}")
        print(f"   • Analiz Aralığı: {self.config.ANALYSIS_INTERVAL} dakika")
        print(f"   • Saatlik Max Sinyal: {self.config.MAX_SIGNALS_PER_HOUR}")
        print(f"   • Telegram Token: {self.config.TELEGRAM_BOT_TOKEN[:20]}...")
        print("=" * 60)
        
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
        
        # Haftalık performans raporu
        schedule.every().week.do(self._weekly_performance_report)
        
        self.logger.info("Zamanlanmış görevler ayarlandı")
        
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
                    
                    # Teknik analiz yap
                    analysis = self.technical_analyzer.analyze_coin(symbol)
                    if not analysis:
                        print(f"    ❌ {symbol} - Analiz verisi alınamadı")
                        continue
                        
                    # Sinyal üret
                    signal = self.technical_analyzer.generate_trading_signal(analysis)
                    if signal:
                        print(f"    🎯 {symbol} - Potansiyel {signal['signal_type']} sinyali!")
                        print(f"       💪 Güven: {signal['confidence']:.1f}%")
                        print(f"       ⚡ Gücü: {signal['signal_strength']['dominant_signal']}")
                        
                        # AI tahmin kontrolü
                        if self.ai_optimizer.is_trained:
                            success_probability = self.ai_optimizer.predict_signal_success(analysis)
                            if success_probability and success_probability < 0.6:
                                print(f"       🤖 AI tahmin düşük: {success_probability:.2f} - GEÇİLDİ")
                                self.logger.info(f"AI tahmin düşük {symbol}: {success_probability:.2f}")
                                continue
                            else:
                                print(f"       🤖 AI onayı: {success_probability:.2f}" if success_probability else "       🤖 AI henüz eğitilmedi")
                                
                        # Hızlı validation
                        print(f"       🔍 Hızlı doğrulama yapılıyor...")
                        validation_result = await self.signal_validator.quick_validate_signal(signal)
                        
                        if validation_result['is_validated']:
                            signal['confidence'] += validation_result['confidence_boost']
                            signal['validation_result'] = validation_result
                            potential_signals.append(signal)
                            
                            print(f"       ✅ Doğrulandı! Yeni güven: {signal['confidence']:.1f}%")
                            print(f"       📋 Sebep: {validation_result['reason']}")
                        else:
                            print(f"       ❌ Doğrulanamadı: {validation_result['reason']}")
                    else:
                        # Neden sinyal üretilmediğini açıkla
                        signal_strength = analysis.get('signal_strength', {})
                        long_score = signal_strength.get('long_score', 0)
                        short_score = signal_strength.get('short_score', 0)
                        dominant = signal_strength.get('dominant_signal', 'NEUTRAL')
                        
                        if dominant == 'NEUTRAL':
                            print(f"    ⚪ {symbol} - NÖTRAL (Long: {long_score:.1f}, Short: {short_score:.1f})")
                        elif max(long_score, short_score) < 3.0:
                            print(f"    📉 {symbol} - Sinyal gücü yetersiz ({dominant}: {max(long_score, short_score):.1f}/3.0)")
                        else:
                            print(f"    ⚠️  {symbol} - Risk/Ödül uygun değil")
                            
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
                
                print(f"\n🏆 EN İYİ SİNYAL:")
                print(f"   🪙 Coin: {best_signal['symbol']}")
                print(f"   📊 Tür: {best_signal['signal_type']}")
                print(f"   💪 Güven: {best_signal['confidence']:.1f}%")
                
                if best_signal['confidence'] >= 70:  # Minimum güven eşiği
                    print(f"   ✅ Güven eşiği geçildi! Sinyal gönderiliyor...")
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
            
    async def _send_validated_signal(self, signal: Dict):
        """Doğrulanmış sinyali gönder"""
        try:
            print(f"\n🚀 SİNYAL GÖNDERİLİYOR:")
            print(f"   🪙 {signal['symbol']}")
            print(f"   📊 {signal['signal_type']}")
            print(f"   💰 Giriş: ${signal['entry_price']:.6f}")
            print(f"   🛑 Stop Loss: ${signal['stop_loss']:.6f}")
            print(f"   🎯 TP1: ${signal['take_profits']['tp1']:.6f}")
            
            # Multi-timeframe validation
            print(f"   🔍 Çoklu zaman dilimi doğrulaması...")
            multi_validation = await self.signal_validator.validate_multiple_timeframes(signal)
            if multi_validation['is_validated']:
                signal['confidence'] += multi_validation['confidence_boost']
                print(f"   ✅ Çoklu doğrulama başarılı! Yeni güven: {signal['confidence']:.1f}%")
            else:
                print(f"   ⚠️  Çoklu doğrulama kısmen başarısız")
                
            # Final confidence kontrolü
            if signal['confidence'] < 70:
                print(f"   ❌ Final güven düşük: {signal['confidence']:.1f}% < 70%")
                self.logger.info(f"Final güven düşük: {signal['symbol']} - {signal['confidence']:.1f}%")
                return
                
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
                # Her 6 saatte bir model eğitimini kontrol et
                if len(self.ai_optimizer.performance_data) >= 100:
                    if not self.ai_optimizer.is_trained:
                        self.ai_optimizer.train_prediction_model()
                        
                await asyncio.sleep(21600)  # 6 saat = 21600 saniye
                
            except Exception as e:
                self.logger.error(f"AI optimizasyon hatası: {e}")
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
        """Günlük AI optimizasyonu"""
        try:
            optimization_result = self.ai_optimizer.optimize_parameters()
            self.logger.info(f"Günlük AI optimizasyonu tamamlandı: {optimization_result}")
        except Exception as e:
            self.logger.error(f"Günlük AI optimizasyon hatası: {e}")
            
    def _weekly_performance_report(self):
        """Haftalık performans raporu"""
        try:
            # Performans özeti hazırla
            signal_summary = self.signal_tracker.get_active_signals_summary()
            ai_status = self.ai_optimizer.get_optimization_status()
            
            report = {
                'date': datetime.now().isoformat(),
                'signal_summary': signal_summary,
                'ai_status': ai_status,
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
                
            if self.ai_optimizer:
                self.ai_optimizer._save_performance_data()
                
            self.logger.info("Bot başarıyla durduruldu")
            
        except Exception as e:
            self.logger.error(f"Bot durdurma hatası: {e}")
            
    def get_status(self) -> Dict:
        """Bot durumunu getir"""
        return {
            'is_running': self.is_running,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'signals_sent_hour': self.signals_sent_hour,
            'max_signals_per_hour': self.config.MAX_SIGNALS_PER_HOUR,
            'active_signals': len(self.signal_tracker.active_signals) if self.signal_tracker else 0,
            'telegram_users': len(self.telegram_bot.chat_ids) if self.telegram_bot else 0,
            'ai_trained': self.ai_optimizer.is_trained if self.ai_optimizer else False
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