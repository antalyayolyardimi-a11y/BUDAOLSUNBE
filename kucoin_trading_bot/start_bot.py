#!/usr/bin/env python3
"""
KuCoin Professional Trading Bot
Quick Start Script - TEK TIK İLE ÇALIŞIR!
"""

import subprocess
import sys
import os
import shutil
import platform

def find_python_executable():
    """Python executable'ın doğru yolunu bul"""
    possible_paths = [
        "C:/Users/user/BUDAOLSUNBE/.venv/Scripts/python.exe",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "Scripts", "python.exe"),
        sys.executable
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return sys.executable

def setup_environment():
    """Tüm ortam kurulumunu yap"""
    print("🔧 Ortam hazırlanıyor...")
    
    # Script dizinine geç
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Çalışma dizini: {script_dir}")
    
    # Python executable bul
    python_exe = find_python_executable()
    print(f"🐍 Python: {python_exe}")
    
    return python_exe, script_dir

def install_packages(python_exe):
    """Gerekli paketleri kur"""
    print("📦 Paket kurulumu kontrol ediliyor...")
    
    # Önemli paketleri tek tek kur
    critical_packages = [
        'schedule', 'requests', 'python-dotenv', 'pandas', 
        'numpy', 'python-telegram-bot'
    ]
    
    for package in critical_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} yüklü")
        except ImportError:
            print(f"📥 {package} kuruluyor...")
            try:
                subprocess.run([python_exe, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                print(f"✅ {package} kuruldu")
            except subprocess.CalledProcessError:
                print(f"⚠️  {package} kurulumunda sorun, devam ediliyor...")

def create_directories():
    """Gerekli klasörleri oluştur"""
    print("📁 Klasörler oluşturuluyor...")
    directories = ['logs', 'data', 'backup']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ {directory} klasörü hazır")

def setup_env_file():
    """Env dosyasını oluştur"""
    print("⚙️  Konfigürasyon dosyası kontrol ediliyor...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ .env dosyası oluşturuldu")
        else:
            # Temel .env dosyası oluştur
            env_content = """# Environment Variables
TELEGRAM_BOT_TOKEN=8484153893:AAEybdOXrMvpDEjAg-o2KiCFYWtDSL1PxH4
TELEGRAM_CHAT_ID=auto_detect

# KuCoin API Credentials (Optional)
KUCOIN_API_KEY=
KUCOIN_SECRET_KEY=
KUCOIN_PASSPHRASE=
KUCOIN_SANDBOX=False

# Trading Parameters
MIN_VOLUME_USDT=100000
ANALYSIS_INTERVAL=5
VALIDATION_INTERVAL=5
MAX_SIGNALS_PER_HOUR=12

# AI Optimization
LEARNING_RATE=0.01
OPTIMIZATION_INTERVAL=24
"""
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            print("✅ .env dosyası oluşturuldu")
    else:
        print("✅ .env dosyası mevcut")

def start_bot(python_exe):
    """Bot'u başlat"""
    print("\n� Bot başlatılıyor...")
    print("=" * 60)
    
    try:
        # main.py'yi çalıştır
        subprocess.run([python_exe, 'main.py'])
    except KeyboardInterrupt:
        print("\n🛑 Bot kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n❌ Bot başlatma hatası: {e}")
        print("💡 Manuel başlatma komutu:")
        print(f"   {python_exe} main.py")

def main():
    """Ana fonksiyon - TEK TIK İLE HER ŞEY!"""
    print("🚀 KuCoin Trading Bot - TEK TIK BAŞLATMA")
    print("=" * 60)
    print("� Artık hiçbir sorun yaşamayacaksın!")
    print("=" * 60)
    
    try:
        # 1. Ortamı hazırla
        python_exe, script_dir = setup_environment()
        
        # 2. Paketleri kur
        install_packages(python_exe)
        
        # 3. Klasörleri oluştur
        create_directories()
        
        # 4. Env dosyasını hazırla
        setup_env_file()
        
        print("\n✅ TÜM HAZIRLIKLAR TAMAMLANDI!")
        print("🎯 Bot tamamen hazır, başlatılıyor...")
        
        # 5. Bot'u başlat
        start_bot(python_exe)
        
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        print("� Bu hatayı göster, düzeltelim!")

if __name__ == "__main__":
    main()