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
/stop - Sinyal almayı durdur

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
        """Trading sinyali gönder"""
        if not self.chat_ids:
            self.logger.warning("Gönderilecek chat ID yok")
            return False
            
        try:
            # Sinyal mesajını formatla
            message = self.format_signal_message(signal)
            
            # Tüm chat ID'lere gönder
            success_count = 0
            for chat_id in self.chat_ids.copy():
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Sinyal gönderme hatası {chat_id}: {e}")
                    # Geçersiz chat ID'yi kaldır
                    if "chat not found" in str(e).lower():
                        self.chat_ids.discard(chat_id)
                        
            # Chat ID'leri güncelle
            if success_count != len(self.chat_ids):
                self.save_chat_ids()
                
            self.logger.info(f"Sinyal gönderildi: {success_count}/{len(self.chat_ids)} kullanıcı")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Sinyal gönderme genel hatası: {e}")
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
• Zaman: {datetime.now().strftime('%H:%M:%S')}

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
        """Chat ID'leri dosyadan yükle"""
        try:
            with open('data/chat_ids.json', 'r') as f:
                chat_ids_data = json.load(f)
                self.chat_ids = set(chat_ids_data.get('chat_ids', []))
                
            self.logger.info(f"{len(self.chat_ids)} chat ID yüklendi")
            
        except FileNotFoundError:
            self.logger.info("Chat IDs dosyası bulunamadı, yeni liste oluşturuluyor")
            self.chat_ids = set()
        except Exception as e:
            self.logger.error(f"Chat ID yükleme hatası: {e}")
            self.chat_ids = set()
            
    def save_chat_ids(self):
        """Chat ID'leri dosyaya kaydet"""
        try:
            chat_ids_data = {
                'chat_ids': list(self.chat_ids),
                'last_updated': datetime.now().isoformat()
            }
            
            with open('data/chat_ids.json', 'w') as f:
                json.dump(chat_ids_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Chat ID kaydetme hatası: {e}")
            
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
            
    def get_stats(self) -> Dict:
        """Bot istatistiklerini getir"""
        return {
            'active_chat_ids': len(self.chat_ids),
            'bot_status': 'active' if self.bot else 'inactive',
            'last_updated': datetime.now().isoformat()
        }