"""
Smart Cache System avec multi-sources API et TTL intelligent
Techniques anti-rate-limiting:
1. Cache avec TTL adaptatif (plus long si rate limited)
2. Rotation entre APIs (CoinGecko, CMC, CoinPaprika)
3. Stale-while-revalidate (retourne cache expiré pendant refresh background)
4. Circuit breaker (désactive API temporairement si trop d'erreurs)
"""
import time
import requests
from typing import Optional, Dict, Callable, Any
from datetime import datetime, timedelta
from threading import Lock
import asyncio
from functools import wraps

# Configuration
CACHE_TTL_DEFAULT = 60  # 1 minute pour données live
CACHE_TTL_RATE_LIMITED = 300  # 5 minutes si rate limited
CACHE_TTL_STALE = 600  # 10 minutes pour stale data
CIRCUIT_BREAKER_THRESHOLD = 3  # 3 échecs = circuit ouvert
CIRCUIT_BREAKER_TIMEOUT = 120  # 2 minutes avant retry


class CircuitBreaker:
    """Désactive temporairement une API si trop d'erreurs"""
    
    def __init__(self, threshold: int = CIRCUIT_BREAKER_THRESHOLD, timeout: int = CIRCUIT_BREAKER_TIMEOUT):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Reset après succès"""
        self.failures = 0
        self.is_open = False
    
    def record_failure(self):
        """Enregistre échec"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.threshold:
            self.is_open = True
            print(f"⚠️  Circuit breaker OPEN - API désactivée pour {self.timeout}s")
    
    def can_request(self) -> bool:
        """Vérifie si on peut utiliser l'API"""
        if not self.is_open:
            return True
        
        # Check if timeout expired
        if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
            print(f"🔄 Circuit breaker RESET - réactivation API")
            self.is_open = False
            self.failures = 0
            return True
        
        return False


class SmartCache:
    """Cache intelligent avec TTL adaptatif et stale-while-revalidate"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = Lock()
        self._circuit_breakers = {
            'coingecko': CircuitBreaker(),
            'cmc': CircuitBreaker(),
            'coinpaprika': CircuitBreaker()
        }
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.coinpaprika_base = "https://api.coinpaprika.com/v1"
    
    def get(self, key: str, allow_stale: bool = True) -> Optional[Dict]:
        """
        Récupère donnée du cache
        Args:
            key: Cache key
            allow_stale: Si True, retourne données expirées plutôt que None (fallback silencieux)
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            now = time.time()
            age = int(now - entry['timestamp'])
            
            # Fresh data (dans le TTL)
            if age < entry['ttl']:
                return entry['data']
            
            # Stale mais utilisable (extended window - jusqu'à 10 min)
            if allow_stale and age < CACHE_TTL_STALE:
                print(f"📦 Serving STALE cache for {key} (age: {age}s) - fallback silencieux")
                return entry['data']
            
            # Très vieux mais GARDE-LE quand même (ne pas supprimer = fallback ultime)
            if allow_stale and age < 3600:  # 1 heure max
                print(f"🆘 EMERGENCY fallback for {key} (age: {age}s) - dernière chance")
                return entry['data']
            
            # Vraiment trop vieux (> 1h) - on supprime
            del self._cache[key]
            return None
    
    def set(self, key: str, data: Any, ttl: int = CACHE_TTL_DEFAULT, is_rate_limited: bool = False, force: bool = False):
        """Stocke donnée avec TTL adaptatif"""
        with self._lock:
            if is_rate_limited:
                ttl = CACHE_TTL_RATE_LIMITED
                print(f"⏰ Extended cache TTL to {ttl}s due to rate limiting")
            
            self._cache[key] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl
            }
    
    def clear(self):
        """Vide le cache"""
        with self._lock:
            self._cache.clear()
    
    def get_circuit_breaker(self, api_name: str) -> CircuitBreaker:
        """Récupère circuit breaker pour une API"""
        return self._circuit_breakers.get(api_name, CircuitBreaker())
    
    def fetch_with_fallback(
        self,
        key: str,
        primary_fetcher: Callable,
        fallback_fetchers: list[Callable] = None,
        ttl: int = CACHE_TTL_DEFAULT,
        never_fail: bool = True  # Mode prod: JAMAIS d'erreur, toujours retourner quelque chose
    ) -> Optional[Dict]:
        """
        Stratégie ultra-résiliente:
        1. Vérifier cache (fresh)
        2. Essayer API primaire (CoinGecko)
        3. Si échec/rate limit, essayer APIs secondaires (CMC, CoinPaprika)
        4. Retourner stale cache (même très vieux) si toutes APIs échouent
        5. Mode never_fail: TOUJOURS retourner des données (même anciennes)
        """
        # 1. Check cache first (fresh data)
        cached = self.get(key, allow_stale=False)  # Fresh only
        if cached:
            return cached
        
        # 2. Try primary API with circuit breaker
        cb_primary = self.get_circuit_breaker('coingecko')
        if cb_primary.can_request():
            try:
                data = primary_fetcher()
                if data:
                    cb_primary.record_success()
                    self.set(key, data, ttl=ttl)
                    print(f"✅ Primary API success: {key}")
                    return data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"⚠️  Rate limited on primary API - fallback mode activated")
                    cb_primary.record_failure()
                else:
                    cb_primary.record_failure()
            except Exception as e:
                print(f"❌ Primary API error: {e}")
                cb_primary.record_failure()
        
        # 3. Try fallback APIs
        if fallback_fetchers:
            for idx, fetcher in enumerate(fallback_fetchers):
                try:
                    data = fetcher()
                    if data:
                        self.set(key, data, ttl=ttl, is_rate_limited=True)
                        print(f"✅ Fallback API #{idx+1} success: {key}")
                        return data
                except Exception as e:
                    print(f"❌ Fallback API #{idx+1} error: {e}")
        
        # 4. FALLBACK ULTIME: Retourner stale cache même très vieux (never_fail mode)
        if never_fail:
            stale_data = self.get(key, allow_stale=True)
            if stale_data:
                print(f"🆘 NEVER-FAIL mode: serving old cache for {key}")
                return stale_data
        
        # 5. Vraiment rien disponible
        return None
    
    def fetch_coinpaprika_markets(self):
        """Alternative à CoinGecko via CoinPaprika"""
        try:
            url = f"{self.coinpaprika_base}/coins"
            params = {'limit': 100}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            coins = []
            for coin in data[:50]:  # Top 50
                coins.append({
                    'id': coin.get('id', ''),
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name', ''),
                    'rank': coin.get('rank', 0)
                })
            
            return {'coins': coins, 'total': len(coins)}
        except Exception as e:
            print(f"CoinPaprika error: {e}")
            return None


# Global cache instance
smart_cache = SmartCache()


def cached_endpoint(ttl: int = CACHE_TTL_DEFAULT):
    """
    Décorateur pour endpoints API avec cache intelligent
    Usage:
        @cached_endpoint(ttl=120)
        async def get_coins():
            return fetch_data()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            cached = smart_cache.get(cache_key)
            if cached:
                return cached
            
            # Fetch fresh data
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result:
                smart_cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
