#!/usr/bin/env python3
"""
KuCoin Professional Trading Bot
Quick Start Script
"""

import subprocess
import sys
import os

def main():
    print("🚀 KuCoin Trading Bot Hızlı Başlatma")
    print("=" * 50)
    
    # Dizin kontrolü
    if not os.path.exists('main.py'):
        print("❌ main.py bulunamadı. Doğru dizinde olduğunuzdan emin olun.")
        return
        
    # .env kontrolü
    if not os.path.exists('.env'):
        print("⚠️  .env dosyası bulunamadı, oluşturuluyor...")
        if os.path.exists('.env.example'):
            subprocess.run(['cp', '.env.example', '.env'])
            print("✅ .env dosyası oluşturuldu")
        else:
            print("❌ .env.example bulunamadı")
            return
            
    # Virtual environment kontrolü
    if not os.path.exists('venv'):
        print("📦 Virtual environment oluşturuluyor...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
        
    # Paket kurulumu kontrolü
    try:
        import requests
        import pandas
        print("✅ Gerekli paketler yüklü")
    except ImportError:
        print("📚 Gerekli paketler yükleniyor...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
    # Gerekli klasörleri oluştur
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print("\n✅ Tüm kontroler tamamlandı!")
    print("🚀 Bot başlatılıyor...\n")
    
    # Bot'u çalıştır
    try:
        subprocess.run([sys.executable, 'main.py'])
    except KeyboardInterrupt:
        print("\n🛑 Bot durduruldu")

if __name__ == "__main__":
    main()