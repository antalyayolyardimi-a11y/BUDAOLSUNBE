import hashlib
import hmac
import base64
import time
import json
import requests
import logging
from typing import Dict, List, Optional
from config import Config

class KuCoinAPI:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = 'https://api.kucoin.com'  # Always use public API
        self.api_key = config.KUCOIN_API_KEY
        self.secret_key = config.KUCOIN_SECRET_KEY
        self.passphrase = config.KUCOIN_PASSPHRASE
        self.logger = logging.getLogger(__name__)
        
        # Public API endpoints (no auth required)
        self.use_public_api = not all([self.api_key, self.secret_key, self.passphrase])
        if self.use_public_api:
            print("🌐 KuCoin Public API kullanılıyor (API key gerekli değil)")
            self.logger.info("Using KuCoin Public API (no authentication required)")
        else:
            print("🔐 KuCoin Private API kullanılıyor")
            self.logger.info("Using KuCoin Private API")
        
    def _generate_signature(self, timestamp: str, method: str, endpoint: str, body: str = '') -> str:
        """KuCoin API için imza oluşturma"""
        message = timestamp + method + endpoint + body
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return signature
        
    def _generate_passphrase_signature(self) -> str:
        """Passphrase imzası oluşturma"""
        return base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                self.passphrase.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """API isteği yapma"""
        url = self.base_url + endpoint
        
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url += '?' + query_string
            
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Eğer private API kullanılıyorsa imza ekle
        if not self.use_public_api:
            timestamp = str(int(time.time() * 1000))
            request_endpoint = endpoint
            if params:
                request_endpoint += '?' + query_string
                
            body = json.dumps(data) if data else ''
            signature = self._generate_signature(timestamp, method, request_endpoint, body)
            passphrase_sig = self._generate_passphrase_signature()
            
            headers.update({
                'KC-API-SIGN': signature,
                'KC-API-TIMESTAMP': timestamp,
                'KC-API-KEY': self.api_key,
                'KC-API-PASSPHRASE': passphrase_sig,
                'KC-API-KEY-VERSION': '2'
            })
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Desteklenmeyen HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API isteği başarısız: {e}")
            # Public endpoint'leri dene
            return self._fallback_public_request(endpoint, params)
            
    def _fallback_public_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Public API fallback"""
        try:
            url = self.base_url + endpoint
            if params:
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                url += '?' + query_string
                
            headers = {'Content-Type': 'application/json'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Fallback request failed: {e}")
            return {}
            
    def get_market_symbols(self) -> List[Dict]:
        """Tüm market sembollerini getir"""
        endpoint = '/api/v1/symbols'
        response = self._make_request('GET', endpoint)
        
        if response.get('code') == '200000':
            return response.get('data', [])
        else:
            self.logger.error(f"Market sembolleri alınamadı: {response}")
            return []
            
    def get_24hr_stats(self) -> List[Dict]:
        """24 saatlik istatistikleri getir"""
        endpoint = '/api/v1/market/allTickers'
        response = self._make_request('GET', endpoint)
        
        if response.get('code') == '200000':
            return response.get('data', {}).get('ticker', [])
        else:
            self.logger.error(f"24hr stats alınamadı: {response}")
            return []
            
    def get_high_volume_coins(self, min_volume_usdt: float = 100000) -> List[Dict]:
        """Hacmi yüksek coinleri getir"""
        stats = self.get_24hr_stats()
        symbols = self.get_market_symbols()
        
        # Sembol bilgilerini dict'e çevir
        symbol_info = {s['symbol']: s for s in symbols if s['quoteCurrency'] == 'USDT'}
        
        high_volume_coins = []
        
        for stat in stats:
            symbol = stat.get('symbol')
            if symbol in symbol_info:
                try:
                    volume_usdt = float(stat.get('volValue', 0))
                    if volume_usdt >= min_volume_usdt:
                        coin_data = {
                            'symbol': symbol,
                            'base_currency': symbol_info[symbol]['baseCurrency'],
                            'quote_currency': symbol_info[symbol]['quoteCurrency'],
                            'volume_usdt': volume_usdt,
                            'price': float(stat.get('last', 0)),
                            'change_rate': float(stat.get('changeRate', 0)),
                            'high_24h': float(stat.get('high', 0)),
                            'low_24h': float(stat.get('low', 0)),
                            'volume_24h': float(stat.get('vol', 0))
                        }
                        high_volume_coins.append(coin_data)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Coin verisi işlenirken hata: {symbol} - {e}")
                    continue
                    
        # Hacime göre sırala
        high_volume_coins.sort(key=lambda x: x['volume_usdt'], reverse=True)
        
        self.logger.info(f"{len(high_volume_coins)} adet yüksek hacimli coin bulundu")
        return high_volume_coins
        
    def get_klines(self, symbol: str, interval: str = '15min', start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[List]:
        """Mum verileri getir"""
        endpoint = '/api/v1/market/candles'
        params = {
            'symbol': symbol,
            'type': interval
        }
        
        if start_time:
            params['startAt'] = start_time
        if end_time:
            params['endAt'] = end_time
            
        response = self._make_request('GET', endpoint, params=params)
        
        if response.get('code') == '200000':
            klines = response.get('data', [])
            # KuCoin API'si tersine sıralı döndürür, düzeltelim
            klines.reverse()
            return klines
        else:
            self.logger.error(f"Klines alınamadı {symbol}: {response}")
            return []
            
    def get_real_time_price(self, symbol: str) -> Optional[float]:
        """Gerçek zamanlı fiyat getir"""
        endpoint = f'/api/v1/market/orderbook/level1'
        params = {'symbol': symbol}
        
        response = self._make_request('GET', endpoint, params=params)
        
        if response.get('code') == '200000':
            data = response.get('data', {})
            return float(data.get('price', 0))
        else:
            self.logger.error(f"Gerçek zamanlı fiyat alınamadı {symbol}: {response}")
            return None