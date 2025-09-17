# KuCoin Professional Trading Bot

## 🚀 Hızlı Başlatma

```bash
cd kucoin_trading_bot
python start_bot.py
```

## ✨ Özellikler
- 🔄 **5 dakikada bir otomatik analiz**
- 📊 KuCoin Public API (API key gerektirmez)
- 🧠 AI destekli sinyal optimizasyonu
- 📱 Telegram otomatik bildirim sistemi
- 🎯 TP1/TP2/TP3 ve Stop Loss takibi
- 🔍 5 dakikalık grafik doğrulama sistemi
- 📋 Detaylı terminal çıktıları

## 📱 Telegram Bot Token
**Hazır Token:** `8484153893:AAEybdOXrMvpDEjAg-o2KiCFYWtDSL1PxH4`

## 🔧 Manuel Kurulum
```bash
# 1. Gerekli paketleri yükle
pip install -r requirements.txt

# 2. Gerekli klasörleri oluştur
mkdir -p logs data

# 3. Bot'u başlat
python main.py
```

## 📊 Analiz Detayları

Bot terminalde her analiz için şunları gösterir:

### ✅ Sinyal Bulunduğunda:
```
🎯 LONG SİNYALİ BULUNDU!
   🪙 BTC-USDT
   💪 Güven: 85.2%
   ⚡ Gücü: LONG
   🤖 AI onayı: 0.78
   ✅ Doğrulandı! Sebep: Güçlü anlık doğrulama
```

### ❌ Sinyal Bulunamadığında:
```
⚪ ETH-USDT - NÖTRAL (Long: 2.1, Short: 2.3)
📉 ADA-USDT - Sinyal gücü yetersiz (LONG: 2.8/3.0)
⚠️  DOT-USDT - Risk/Ödül uygun değil
```

### 📋 Her Analiz Sonunda:
```
📋 Analiz özeti:
   💹 Toplam coin: 45
   🔍 Analiz edilen: 30
   🎯 Potansiyel sinyal: 2
   ❌ Bu döngüde sinyal bulunamadı
```

## 🎯 Sinyal Kriterleri

### LONG Sinyali İçin:
- RSI < 40 (oversold)
- MACD histogram pozitif
- Bollinger Bands alt bantlarda
- Volume konfirmasyonu (CMF > 0)
- Trend gücü ADX > 25

### SHORT Sinyali İçin:
- RSI > 60 (overbought)
- MACD histogram negatif
- Bollinger Bands üst bantlarda
- Volume konfirmasyonu (CMF < 0)
- Trend gücü ADX > 25

## 📈 Terminal Çıktı Örnekleri

```
🔍 ANALİZ BAŞLADI - 14:30:25
================================================================
📊 Analiz #1 başlıyor...
🔄 Yüksek hacimli coinler alınıyor...
✅ 45 yüksek hacimli coin bulundu
🎯 İlk 30 coin analiz ediliyor...

  📈 [1/30] BTC-USDT analiz ediliyor...
    🎯 BTC-USDT - Potansiyel LONG sinyali!
       💪 Güven: 82.1%
       ⚡ Gücü: LONG
       🤖 AI onayı: 0.78
       🔍 Hızlı doğrulama yapılıyor...
       ✅ Doğrulandı! Yeni güven: 87.1%

  📈 [2/30] ETH-USDT analiz ediliyor...
    ⚪ ETH-USDT - NÖTRAL (Long: 2.1, Short: 2.3)

🏆 EN İYİ SİNYAL:
   🪙 Coin: BTC-USDT
   📊 Tür: LONG
   💪 Güven: 87.1%
   ✅ Güven eşiği geçildi! Sinyal gönderiliyor...

🚀 SİNYAL GÖNDERİLİYOR:
   ✅ SİNYAL BAŞARIYLA GÖNDERİLDİ!
   🆔 Sinyal ID: abc123
   ⏰ Zaman: 14:30:45
================================================================
```

## 🔧 Yapılandırma

`.env` dosyası otomatik oluşturulur ve şunları içerir:

```env
TELEGRAM_BOT_TOKEN=8484153893:AAEybdOXrMvpDEjAg-o2KiCFYWtDSL1PxH4
MIN_VOLUME_USDT=100000
ANALYSIS_INTERVAL=5
MAX_SIGNALS_PER_HOUR=12
```

## 🛡️ Güvenlik
- API anahtarları opsiyonel (Public API kullanılır)
- Tüm işlemler loglanır
- Sadece yetkili chat ID'lere sinyal gönderir
- Rate limiting entegrasyonu

## 📞 Destek
Bot çalışırken herhangi bir sorun yaşarsanız:
1. Terminal çıktılarını kontrol edin
2. `logs/` klasöründeki log dosyalarını inceleyin
3. Telegram'da `/status` komutunu deneyin