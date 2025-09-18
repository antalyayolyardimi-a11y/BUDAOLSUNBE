import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from config import Config

class TelegramBot:
    def __init__(self, config: Config):
        self.config = config
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.authorized_users = set()
        self.chat_ids = set()
        self.logger = logging.getLogger(__name__)
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        
    async def initialize(self):
        """Bot'u başlat"""
        try:
            if not self.bot_token:
                raise ValueError("Telegram bot token eksik!")
                
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot
            
            # Command handler'ları ekle
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("aireport", self.ai_report_command))  # AI rapor komutu
            self.application.add_handler(CommandHandler("stop", self.stop_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Chat ID'leri yükle
            self.load_chat_ids()
            
            self.logger.info("Telegram bot başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Bot başlatma hatası: {e}")
            raise
            
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start komutu"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        # Chat ID'yi kaydet
        self.chat_ids.add(chat_id)
        self.save_chat_ids()
        
        welcome_message = f"""
🤖 **KuCoin Trading Bot**'a hoş geldiniz!

Merhaba {user.first_name}! 

Bu bot size KuCoin borsasında yüksek hacimli coinlerin teknik analizini yaparak profesyonel trading sinyalleri gönderir.

**Özellikler:**
• 15 dakikalık grafik analizi
• RSI, MACD, Bollinger Bands analizi
• AI destekli sinyal optimizasyonu
• TP1/TP2/TP3 takibi
• Stop Loss analizi
• 5 dakikalık doğrulama sistemi

**Komutlar:**
/help - Yardım menüsü
/status - Bot durumu
/stats - Performans istatistikleri

Chat ID'niz: `{chat_id}`

🚀 **Bot aktif!** Sinyaller otomatik olarak gönderilecektir.
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        self.logger.info(f"Yeni kullanıcı: {user.first_name} - Chat ID: {chat_id}")
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yardım komutu"""
        help_text = """
📚 **KuCoin Trading Bot - Yardım**

**Komutlar:**
/start - Bot'u başlat ve kayıt ol
/help - Bu yardım menüsünü göster
/status - Bot'un mevcut durumunu görüntüle
/stats - Performans istatistiklerini görüntüle
/aireport - 🤖 AI Optimizer performans raporu
/stop - Sinyal almayı durdur

**AI Özellikleri:**
🤖 Otomatik parametre optimizasyonu
📊 Başarı oranı takibi
🎯 Akıllı sinyal filtreleme
📈 Strateji analizi

**Sinyal Formatı:**
🔴/🟢 Sinyal Türü (LONG/SHORT)
💰 Giriş Fiyatı
🎯 TP1, TP2, TP3 
🛑 Stop Loss
📊 Güven Oranı
⚡ Sinyal Gücü

**Risk Uyarısı:**
Bu bot sadece analiz amaçlıdır. Yatırım kararlarınızı alırken kendi araştırmanızı yapın.
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Durum komutu"""
        try:
            # Bot durumu mesajı oluştur
            status_message = f"""
📊 **Bot Durumu**

⏰ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}
🎯 Aktif Chat ID'ler: {len(self.chat_ids)}
🤖 Bot Durumu: ✅ Aktif

📈 **Analiz Parametreleri:**
• Minimum Hacim: ${self.config.MIN_VOLUME_USDT:,.0f}
• Analiz Aralığı: {self.config.ANALYSIS_INTERVAL} dakika
• Doğrulama Aralığı: {self.config.VALIDATION_INTERVAL} dakika
• Saatlik Max Sinyal: {self.config.MAX_SIGNALS_PER_HOUR}

🔄 **Son 24 Saat:**
• Analiz Edilen Coin: [Yakında]
• Gönderilen Sinyal: [Yakında]
• Başarı Oranı: [Yakında]
            """
            
            await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            self.logger.error(f"Status komutu hatası: {e}")
            await update.message.reply_text("Durum bilgisi alınırken hata oluştu.")
            
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """İstatistik komutu"""
        try:
            # İstatistik verilerini yükle (şimdilik placeholder)
            stats_message = """
📊 **Performans İstatistikleri**

📈 **Genel Performans:**
• Toplam Sinyal: [Yakında]
• Başarılı Sinyal: [Yakında]
• Başarı Oranı: [Yakında]%
• Ortalama Kar: [Yakında]%

🎯 **TP Başarı Oranları:**
• TP1: [Yakında]%
• TP2: [Yakında]%
• TP3: [Yakında]%

📊 **Sinyal Türü Performansı:**
• LONG Başarı: [Yakında]%
• SHORT Başarı: [Yakında]%

🤖 **AI Optimizasyon:**
• Son Optimizasyon: [Yakında]
• Model Eğitimi: [Yakında]
• Önerilen Değişiklikler: [Yakında]
            """
            
            await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            self.logger.error(f"Stats komutu hatası: {e}")
            await update.message.reply_text("İstatistik bilgisi alınırken hata oluştu.")
            
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop komutu"""
        chat_id = update.effective_chat.id
        
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
            self.save_chat_ids()
            
        stop_message = """
🛑 **Sinyal Durduruldu**

Chat ID'niz listeden çıkarıldı. Artık sinyal almayacaksınız.

Yeniden sinyal almak için /start komutunu kullanın.

Bot'u kullandığınız için teşekkürler! 👋
        """
        
        await update.message.reply_text(stop_message, parse_mode=ParseMode.MARKDOWN)
        self.logger.info(f"Kullanıcı çıkarıldı - Chat ID: {chat_id}")
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genel mesaj işleyici"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.lower()
        
        # Chat ID'yi otomatik kaydet
        if chat_id not in self.chat_ids:
            self.chat_ids.add(chat_id)
            self.save_chat_ids()
            
        # Basit cevaplar
        if "merhaba" in message_text or "selam" in message_text:
            await update.message.reply_text("Merhaba! Bot aktif durumda. /help komutu ile yardım alabilirsiniz.")
        elif "teşekkür" in message_text:
            await update.message.reply_text("Rica ederim! İyi tradeler dilerim. 📈")
        else:
            await update.message.reply_text("Komutlar için /help yazabilirsiniz.")
            
    async def send_signal(self, signal: Dict) -> bool:
        """Trading sinyali gönder - Geliştirilmiş hata toleransı"""
        if not self.chat_ids:
            self.logger.warning("Gonderilecek chat ID yok - Lutfen /start yazin")
            return False
            
        try:
            # 🚀 Bot bağlantısını yenile (timeout sorunlarına karşı)
            await self._refresh_bot_connection()
            
            # Chat ID'leri yeniden yükle (güncellikleri yakala)
            self.load_chat_ids()
            
            if not self.chat_ids:
                self.logger.warning("Chat ID'ler yuklenmedi - Kullanici kaydi gerekli")
                return False
            
            # Sinyal mesajını formatla
            message = self.format_signal_message(signal)
            
            # Tüm chat ID'lere gönder - timeout ile
            success_count = 0
            failed_chats = []
            
            # 🚀 Her gönderim öncesi kısa bekle (rate limiting)
            total_chats = len(self.chat_ids)
            self.logger.info(f"Sinyal gonderiliyor: {total_chats} kullaniciya")
            
            for i, chat_id in enumerate(self.chat_ids.copy(), 1):
                try:
                    # Her gönderimde kısa bekle
                    if i > 1:
                        await asyncio.sleep(0.5)  # 500ms bekle
                    
                    # 🚀 Timeout ve retry ekle
                    max_retries = 3
                    retry_count = 0
                    
                    while retry_count < max_retries:
                        try:
                            await asyncio.wait_for(
                                self.bot.send_message(
                                    chat_id=chat_id,
                                    text=message,
                                    parse_mode=ParseMode.MARKDOWN
                                ),
                                timeout=5.0  # 5 saniye timeout
                            )
                            success_count += 1
                            self.logger.info(f"Sinyal gonderildi: {chat_id}")
                            break  # Başarılı, döngüden çık
                            
                        except asyncio.TimeoutError:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.logger.warning(f"Timeout {chat_id}, deneme {retry_count}/{max_retries}")
                                await asyncio.sleep(2)  # 2 saniye bekle ve tekrar dene
                            else:
                                self.logger.error(f"Timeout {chat_id}: {max_retries} deneme basarisiz")
                                failed_chats.append(chat_id)
                                break
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    self.logger.error(f"Sinyal gonderme hatasi {chat_id}: {e}")
                    
                    # Geçersiz chat ID'yi kaldır
                    if any(err in error_msg for err in ["chat not found", "blocked", "deactivated"]):
                        self.logger.warning(f"Gecersiz chat ID kaldirilıyor: {chat_id}")
                        self.chat_ids.discard(chat_id)
                    else:
                        failed_chats.append(chat_id)
                        
            # Chat ID'leri güncelle (başarısızsa kaydet)
            if len(self.chat_ids) > 0:
                self.save_chat_ids()
                
            # Sonuç raporu
            total_chats = len(self.chat_ids) + len(failed_chats)
            if success_count > 0:
                self.logger.info(f"Sinyal basarili: {success_count}/{total_chats} kullanici")
            else:
                self.logger.warning(f"Hicbir kullaniciya sinyal gonderilemedi! Chat ID kontrol edin.")
                
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Sinyal gonderme kritik hatasi: {e}")
            return False
            
    def format_signal_message(self, signal: Dict) -> str:
        """Sinyal mesajını formatla"""
        signal_type = signal['signal_type']
        symbol = signal['symbol']
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        
        # SMC strategy'de take_profits yerine take_profit_1 var
        if 'take_profits' in signal:
            take_profits = signal['take_profits']
            tp1, tp2, tp3 = take_profits['tp1'], take_profits['tp2'], take_profits['tp3']
        else:
            # Yeni SMC format
            tp1 = signal.get('take_profit_1', signal.get('tp1', entry_price))
            tp2 = signal.get('take_profit_2', signal.get('tp2', entry_price))  
            tp3 = signal.get('take_profit_3', signal.get('tp3', entry_price))
        
        confidence = signal['confidence']
        
        # M5 Confirmation bilgisi
        m5_info = ""
        if 'm5_confirmation' in signal:
            m5_data = signal['m5_confirmation']
            m5_score = m5_data.get('confirmation_strength', 0)
            candle_analyses = m5_data.get('candle_analysis', [])
            
            m5_info = f"\n📊 **M5 ONAY: {m5_score:.0f}%** ✅"
            if len(candle_analyses) >= 2:
                c1_score = candle_analyses[0].get('points', 0)
                c2_score = candle_analyses[1].get('points', 0)
                m5_info += f"\n   🕯️ 1. Mum: {c1_score}/5 | 2. Mum: {c2_score}/5"
        
        # Risk/Reward hesapla (yoksa hesapla)
        if 'risk_reward_ratio' in signal:
            risk_reward = signal['risk_reward_ratio']
        else:
            # R:R'ı hesapla
            risk = abs(entry_price - stop_loss)
            reward = abs(tp1 - entry_price)
            risk_reward = reward / risk if risk > 0 else 1.0
        
        # Emoji seçimi
        emoji = "🟢" if signal_type == "LONG" else "🔴"
        arrow = "📈" if signal_type == "LONG" else "📉"
        
        # Fiyat formatı belirleme
        def format_price(price):
            if price >= 1:
                return f"${price:.4f}"
            elif price >= 0.01:
                return f"${price:.6f}"
            else:
                return f"${price:.8f}"
        
        # TP seviyeleri için sıralama kontrolü
        if signal_type == "LONG":
            # LONG için TP1 < TP2 < TP3 olmalı
            if not (tp1 < tp2 < tp3):
                tp_list = sorted([tp1, tp2, tp3])
                tp1, tp2, tp3 = tp_list[0], tp_list[1], tp_list[2]
        else:  # SHORT
            # SHORT için TP1 > TP2 > TP3 olmalı  
            if not (tp1 > tp2 > tp3):
                tp_list = sorted([tp1, tp2, tp3], reverse=True)
                tp1, tp2, tp3 = tp_list[0], tp_list[1], tp_list[2]
            # SHORT için TP1 > TP2 > TP3 olmalı  
            if not (tp1 > tp2 > tp3):
                tp_list = sorted([tp1, tp2, tp3], reverse=True)
                tp1, tp2, tp3 = tp_list[0], tp_list[1], tp_list[2]
        
        message = f"""
{emoji} **{signal_type} SİNYALİ** {arrow}

🪙 **Coin:** {symbol}
💰 **Giriş:** {format_price(entry_price)}

🎯 **Take Profit Seviyeleri:**
• TP1: {format_price(tp1)}
• TP2: {format_price(tp2)}  
• TP3: {format_price(tp3)}

🛑 **Stop Loss:** {format_price(stop_loss)}

📊 **Analiz Bilgileri:**
• Güven Oranı: {confidence:.1f}%
• Risk/Ödül: 1:{risk_reward:.2f}
• Zaman: {datetime.now().strftime('%H:%M:%S')}{m5_info}

⚠️ **Risk Uyarısı:** Bu bir yatırım tavsiyesi değildir!
        """
        
        return message
        
    async def send_tp_update(self, signal_id: str, tp_level: int, current_price: float, symbol: str) -> bool:
        """TP seviyesi güncellemesi gönder"""
        try:
            message = f"""
✅ **TP{tp_level} VURDU!**

🪙 **Coin:** {symbol}
💰 **Mevcut Fiyat:** ${current_price:.6f}
🎯 **Seviye:** TP{tp_level}
🕐 **Zaman:** {datetime.now().strftime('%H:%M:%S')}

{"🎉 Tebrikler! Kar almayı unutmayın!" if tp_level >= 2 else "👍 İlk hedef alındı!"}
            """
            
            success_count = 0
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"TP update gönderme hatası {chat_id}: {e}")
                    
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"TP update genel hatası: {e}")
            return False
            
    async def send_sl_update(self, signal_id: str, current_price: float, symbol: str, reason: str = "") -> bool:
        """Stop Loss güncellemesi gönder"""
        try:
            message = f"""
🛑 **STOP LOSS VURDU**

🪙 **Coin:** {symbol}
💰 **Çıkış Fiyatı:** ${current_price:.6f}
🕐 **Zaman:** {datetime.now().strftime('%H:%M:%S')}

📋 **Neden:** {reason if reason else "Teknik seviye kırıldı"}

🤖 **AI Analizi:** Bu veriler analiz edilerek gelecek sinyaller optimize edilecek.
            """
            
            success_count = 0
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"SL update gönderme hatası {chat_id}: {e}")
                    
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"SL update genel hatası: {e}")
            return False
            
    def load_chat_ids(self):
        """Chat ID'leri dosyadan yükle - Geliştirilmiş"""
        try:
            import os
            
            # Dizin yoksa oluştur
            os.makedirs('data', exist_ok=True)
            
            # Dosya varsa yükle
            chat_file = 'data/chat_ids.json'
            if os.path.exists(chat_file):
                with open(chat_file, 'r') as f:
                    chat_ids_data = json.load(f)
                    loaded_ids = chat_ids_data.get('chat_ids', [])
                    
                    # Set'e dönüştür ve mevcut ile birleştir
                    new_ids = set(loaded_ids)
                    if self.chat_ids:
                        new_ids.update(self.chat_ids)
                    self.chat_ids = new_ids
                    
                self.logger.info(f"Chat ID basariyla yuklendi: {len(self.chat_ids)}")
                
                # Yüklenen chat ID'leri hemen kaydet (güvenlik için)
                if self.chat_ids:
                    self.save_chat_ids()
            else:
                self.logger.warning("Chat IDs dosyasi bulunamadi, yeni liste olusturuluyor")
                if not self.chat_ids:
                    self.chat_ids = set()
                # Boş dosya oluştur
                self.save_chat_ids()
                
        except Exception as e:
            self.logger.error(f"❌ Chat ID yükleme hatası: {e}")
            if not self.chat_ids:
                self.chat_ids = set()
            
    def save_chat_ids(self):
        """Chat ID'leri dosyaya kaydet - Geliştirilmiş"""
        try:
            import os
            
            # Dizin yoksa oluştur
            os.makedirs('data', exist_ok=True)
            
            chat_ids_data = {
                'chat_ids': list(self.chat_ids),
                'count': len(self.chat_ids),
                'last_updated': datetime.now().isoformat(),
                'bot_version': '1.0'
            }
            
            # Atomic write (temporary file kullan)
            temp_file = 'data/chat_ids_temp.json'
            final_file = 'data/chat_ids.json'
            
            with open(temp_file, 'w') as f:
                json.dump(chat_ids_data, f, indent=2)
            
            # Dosyayı taşı (atomic operation)
            os.replace(temp_file, final_file)
                
            self.logger.info(f"Chat ID kaydedildi: {len(self.chat_ids)}")
                
        except Exception as e:
            self.logger.error(f"Chat ID kaydetme hatasi: {e}")
            # Temporary file'ı temizle
            try:
                if os.path.exists('data/chat_ids_temp.json'):
                    os.remove('data/chat_ids_temp.json')
            except:
                pass
    
    async def _refresh_bot_connection(self):
        """Bot bağlantısını yenile - timeout sorunlarına karşı"""
        try:
            # Bot instance'ını kontrol et
            if self.bot:
                # Basit bir test isteği gönder
                await asyncio.wait_for(self.bot.get_me(), timeout=3.0)
            else:
                # Bot instance'ını yeniden oluştur
                self.bot = self.application.bot
                
        except Exception as e:
            self.logger.warning(f"Bot baglantisi yenileniyor: {e}")
            try:
                # Application'ı yeniden başlat
                if self.application:
                    self.bot = self.application.bot
            except Exception as ex:
                self.logger.error(f"Bot yenileme hatasi: {ex}")
            
    async def start_polling(self):
        """Bot'u polling modunda başlat"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("Telegram bot polling başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Polling başlatma hatası: {e}")
            raise
            
    async def stop_polling(self):
        """Bot polling'i durdur"""
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            self.logger.info("Telegram bot durduruldu")
            
        except Exception as e:
            self.logger.error(f"Bot durdurma hatası: {e}")
            
    async def ai_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI Optimizer performans raporu komutu"""
        chat_id = update.effective_chat.id
        try:
            # AI Optimizer import et
            from ai_optimizer import AIOptimizer
            
            ai_optimizer = AIOptimizer()
            report = ai_optimizer.generate_performance_report()
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=report,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ AI raporu oluşturulamadı: {e}"
            )
            self.logger.error(f"AI rapor hatası: {e}")
    
    def get_stats(self) -> Dict:
        """Bot istatistiklerini getir"""
        return {
            'active_chat_ids': len(self.chat_ids),
            'bot_status': 'active' if self.bot else 'inactive',
            'last_updated': datetime.now().isoformat()
        }