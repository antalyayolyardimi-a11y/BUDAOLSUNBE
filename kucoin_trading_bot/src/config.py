import os
import logging
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        # Telegram Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        
        # KuCoin API Configuration
        self.KUCOIN_API_KEY = os.getenv('KUCOIN_API_KEY', '')
        self.KUCOIN_SECRET_KEY = os.getenv('KUCOIN_SECRET_KEY', '')
        self.KUCOIN_PASSPHRASE = os.getenv('KUCOIN_PASSPHRASE', '')
        self.KUCOIN_SANDBOX = os.getenv('KUCOIN_SANDBOX', 'False').lower() == 'true'
        
        # Trading Parameters
        self.MIN_VOLUME_USDT = float(os.getenv('MIN_VOLUME_USDT', 100000))
        self.ANALYSIS_INTERVAL = int(os.getenv('ANALYSIS_INTERVAL', 15))
        self.VALIDATION_INTERVAL = int(os.getenv('VALIDATION_INTERVAL', 5))
        self.MAX_SIGNALS_PER_HOUR = int(os.getenv('MAX_SIGNALS_PER_HOUR', 5))
        
        # API Endpoints
        if self.KUCOIN_SANDBOX:
            self.KUCOIN_BASE_URL = 'https://openapi-sandbox.kucoin.com'
        else:
            self.KUCOIN_BASE_URL = 'https://api.kucoin.com'
            
        # Logging Configuration
        self.setup_logging()
        
    def setup_logging(self):
        """Logging konfigürasyonu"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        
        # HTTP isteklerini ve telegram loglarını sustur
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('telegram').setLevel(logging.WARNING)
        logging.getLogger('telegram.ext').setLevel(logging.WARNING)
        
    def validate_config(self):
        """Gerekli konfigürasyonların kontrolü"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(self, var):
                missing_vars.append(var)
                
        if missing_vars:
            raise ValueError(f"Eksik konfigürasyon değişkenleri: {', '.join(missing_vars)}")
            
        # KuCoin API opsiyonel
        if not all([self.KUCOIN_API_KEY, self.KUCOIN_SECRET_KEY, self.KUCOIN_PASSPHRASE]):
            print("⚠️  KuCoin API anahtarları eksik - Public API kullanılacak")
            
        return True