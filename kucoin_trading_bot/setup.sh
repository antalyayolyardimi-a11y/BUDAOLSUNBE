#!/bin/bash

# KuCoin Trading Bot Kurulum ve Çalıştırma Scripti

echo "🤖 KuCoin Professional Trading Bot Kurulumu Başlıyor..."

# Python versiyonu kontrolü
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 bulunamadı. Lütfen Python 3.8+ yükleyin."
    exit 1
fi

echo "✅ Python3 bulundu: $(python3 --version)"

# Virtual environment oluştur
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment oluşturuluyor..."
    python3 -m venv venv
fi

# Virtual environment aktif et
echo "🔄 Virtual environment aktifleştiriliyor..."
source venv/bin/activate

# Gerekli paketleri yükle
echo "📚 Gerekli paketler yükleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

# Gerekli klasörleri oluştur
echo "📁 Gerekli klasörler oluşturuluyor..."
mkdir -p logs
mkdir -p data

# .env dosyası kontrolü
if [ ! -f ".env" ]; then
    echo "⚙️ .env dosyası oluşturuluyor..."
    cp .env.example .env
    echo "❗ Lütfen .env dosyasını API anahtarlarınızla doldurun!"
    echo "📝 Gerekli anahtarlar:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - KUCOIN_API_KEY"
    echo "   - KUCOIN_SECRET_KEY"
    echo "   - KUCOIN_PASSPHRASE"
    exit 1
fi

echo "✅ Kurulum tamamlandı!"
echo ""
echo "🚀 Bot'u başlatmak için:"
echo "   python main.py"
echo ""
echo "⚠️  Önemli Notlar:"
echo "   - Bot 7/24 çalışır, Ctrl+C ile durdurabilirsiniz"
echo "   - Tüm sinyaller logs/ klasörüne kaydedilir"
echo "   - Performans verileri data/ klasöründe saklanır"
echo "   - İlk çalıştırmada Telegram'a /start mesajı gönderin"
echo ""
echo "📊 Bot özellikleri:"
echo "   ✓ 15 dakikalık grafik analizi"
echo "   ✓ RSI, MACD, Bollinger Bands"
echo "   ✓ AI destekli sinyal optimizasyonu"
echo "   ✓ Otomatik TP/SL takibi"
echo "   ✓ 5 dakikalık doğrulama sistemi"
echo "   ✓ Risk yönetimi"
echo ""
echo "💡 Kullanım:"
echo "   - Bot otomatik olarak yüksek hacimli coinleri analiz eder"
echo "   - Güvenilir sinyalleri Telegram'a gönderir"
echo "   - Her sinyali takip eder ve sonuçları bildirir"
echo "   - AI sürekli kendini optimize eder"