"""
Direct API fetching for historical data
Fetches data directly from CoinGecko/CMC APIs instead of relying on scraped data
With cross-validation for enhanced reliability
"""
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import statistics


class DirectAPIFetcher:
    """Fetch historical data directly from external APIs with cross-validation"""
    
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    CMC_BASE = "https://pro-api.coinmarketcap.com/v1"
    CMC_API_KEY = "82f293d614f14f89b9223b51a903ef23"
    
    # Mapping CoinGecko ID → CMC symbol
    COIN_MAPPING = {
        'bitcoin': 'BTC', 'ethereum': 'ETH', 'tether': 'USDT',
        'binancecoin': 'BNB', 'solana': 'SOL', 'usd-coin': 'USDC',
        'ripple': 'XRP', 'dogecoin': 'DOGE', 'cardano': 'ADA',
        'tron': 'TRX', 'avalanche-2': 'AVAX', 'shiba-inu': 'SHIB',
        'polkadot': 'DOT', 'chainlink': 'LINK', 'bitcoin-cash': 'BCH',
        'litecoin': 'LTC'
    }
    
    @staticmethod
    def fetch_coingecko_history(coin_id: str, days: float) -> Optional[List[Dict]]:
        """
        Fetch historical market data from CoinGecko
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin')
            days: Number of days (can be fractional for < 1 day periods)
        
        Returns:
            List of price points with timestamps
        """
        try:
            url = f"{DirectAPIFetcher.COINGECKO_BASE}/coins/{coin_id}/market_chart"
            
            # CoinGecko intervals:
            # - days <= 1: minutely (5min data)
            # - days 1-90: hourly
            # - days > 90: daily
            if days < 1:
                # Pour < 1j, utiliser 1 jour avec données minutely
                params = {
                    'vs_currency': 'usd',
                    'days': '1',  # Must be at least 1 for detailed data
                }
            else:
                params = {
                    'vs_currency': 'usd',
                    'days': str(int(days)),
                }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format: [[timestamp_ms, price], ...]
                prices = data.get('prices', [])
                
                # Filtrer si < 1 jour demandé
                if days < 1:
                    cutoff_time = datetime.now() - timedelta(days=days)
                    prices = [
                        p for p in prices 
                        if datetime.fromtimestamp(p[0] / 1000) >= cutoff_time
                    ]
                
                # Convert to our format
                formatted_prices = []
                for timestamp_ms, price in prices:
                    formatted_prices.append({
                        'timestamp': datetime.fromtimestamp(timestamp_ms / 1000).isoformat(),
                        'price': float(price)
                    })
                
                return formatted_prices
            
            return None
            
        except Exception as e:
            print(f"Error fetching from CoinGecko: {e}")
            return None
    
    @staticmethod
    def fetch_coingecko_current(coin_id: str) -> Optional[Dict]:
        """
        Fetch current coin details from CoinGecko
        
        Returns:
            Complete coin data including price, market cap, volume, etc.
        """
        try:
            url = f"{DirectAPIFetcher.COINGECKO_BASE}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'false',
                'developer_data': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                
                return {
                    'id': coin_id,
                    'symbol': data.get('symbol', '').upper(),
                    'name': data.get('name', ''),
                    'current_price': market_data.get('current_price', {}).get('usd', 0),
                    'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                    'market_cap_rank': market_data.get('market_cap_rank', 0),
                    'total_volume': market_data.get('total_volume', {}).get('usd', 0),
                    'high_24h': market_data.get('high_24h', {}).get('usd', 0),
                    'low_24h': market_data.get('low_24h', {}).get('usd', 0),
                    'price_change_24h': market_data.get('price_change_24h', 0),
                    'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                    'price_change_percentage_7d': market_data.get('price_change_percentage_7d', 0),
                    'price_change_percentage_30d': market_data.get('price_change_percentage_30d', 0),
                    'circulating_supply': market_data.get('circulating_supply', 0),
                    'total_supply': market_data.get('total_supply'),
                    'max_supply': market_data.get('max_supply'),
                    'ath': market_data.get('ath', {}).get('usd', 0),
                    'ath_change_percentage': market_data.get('ath_change_percentage', {}).get('usd', 0),
                    'ath_date': market_data.get('ath_date', {}).get('usd', ''),
                    'atl': market_data.get('atl', {}).get('usd', 0),
                    'atl_change_percentage': market_data.get('atl_change_percentage', {}).get('usd', 0),
                    'atl_date': market_data.get('atl_date', {}).get('usd', ''),
                    'description': data.get('description', {}).get('en', ''),
                    'homepage': data.get('links', {}).get('homepage', [''])[0],
                    'whitepaper': data.get('links', {}).get('whitepaper', ''),
                    'blockchain_site': data.get('links', {}).get('blockchain_site', [])[:3]
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching current data from CoinGecko: {e}")
            return None
    
    @staticmethod
    def fetch_cmc_quotes(symbol: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Fetch latest quotes from CoinMarketCap
        
        Args:
            symbol: CMC symbol (e.g., 'BTC', 'ETH')
            limit: Number of recent quotes to fetch (max 100)
        
        Returns:
            List of price points with timestamps
        """
        try:
            url = f"{DirectAPIFetcher.CMC_BASE}/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': DirectAPIFetcher.CMC_API_KEY,
                'Accept': 'application/json'
            }
            params = {
                'symbol': symbol,
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and symbol in data['data']:
                    quote = data['data'][symbol]['quote']['USD']
                    timestamp = data['data'][symbol]['last_updated']
                    
                    return [{
                        'timestamp': timestamp,
                        'price': float(quote['price'])
                    }]
            
            return None
            
        except Exception as e:
            print(f"Error fetching from CMC: {e}")
            return None
    
    @staticmethod
    def validate_price_data(prices: List[Dict], source: str = "unknown") -> Tuple[bool, str]:
        """
        Validate if price data looks suspicious
        
        Returns:
            (is_valid, reason)
        """
        if not prices or len(prices) < 2:
            return False, "insufficient_data"
        
        try:
            price_values = [p['price'] for p in prices]
            
            # Check 1: Calcul du spread (volatilité)
            min_price = min(price_values)
            max_price = max(price_values)
            spread_pct = ((max_price - min_price) / min_price) * 100
            
            # Check 2: Gaps temporels suspects (> 2x l'intervalle moyen)
            timestamps = [datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00')) for p in prices]
            if len(timestamps) > 1:
                intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                           for i in range(len(timestamps)-1)]
                avg_interval = statistics.mean(intervals)
                max_interval = max(intervals)
                
                if max_interval > avg_interval * 2:
                    return False, f"temporal_gap ({max_interval:.0f}s vs avg {avg_interval:.0f}s)"
            
            # Check 3: Spread anormal (> 5% = suspect pour données récentes)
            if spread_pct > 5.0:
                return False, f"high_volatility ({spread_pct:.2f}%)"
            
            # Check 4: Prix constants (pump & dump ou freeze)
            unique_prices = len(set(price_values))
            if unique_prices < len(price_values) * 0.5:  # < 50% de valeurs uniques
                return False, "price_freeze"
            
            return True, "ok"
            
        except Exception as e:
            return False, f"validation_error: {e}"
    
    @staticmethod
    def cross_validate_with_cmc(coin_id: str, cg_prices: List[Dict]) -> Tuple[Optional[List[Dict]], Dict]:
        """
        OPTION 1: Validation croisée systématique avec moyenne pondérée
        
        Stratégie:
        1. Fetch CoinGecko (déjà fait - passé en param)
        2. Fetch CMC en parallèle
        3. Calculer moyenne pondérée: CG (70%) + CMC (30%)
        4. Retourner données + metadata (source, spread, warnings)
        
        Args:
            coin_id: CoinGecko coin ID
            cg_prices: CoinGecko price data
        
        Returns:
            (validated_prices, metadata)
        """
        metadata = {
            'source': 'coingecko',
            'cmc_validated': False,
            'spread_pct': 0,
            'method': 'single_source'
        }
        
        # Validation basique CoinGecko
        is_valid, reason = DirectAPIFetcher.validate_price_data(cg_prices, "CoinGecko")
        
        # Toujours essayer CMC pour validation (même si CG valide)
        symbol = DirectAPIFetcher.COIN_MAPPING.get(coin_id)
        if not symbol:
            print(f"ℹ️  No CMC mapping for {coin_id}, using CoinGecko only")
            metadata['method'] = 'coingecko_only'
            return cg_prices, metadata
        
        # Fetch CMC
        print(f"🔍 Cross-validating {coin_id} with CMC ({symbol})...")
        cmc_data = DirectAPIFetcher.fetch_cmc_quotes(symbol)
        
        if not cmc_data:
            print(f"⚠️  CMC unavailable, using CoinGecko only")
            metadata['method'] = 'coingecko_fallback'
            return cg_prices, metadata
        
        # Compare latest prices
        cg_latest = cg_prices[-1]['price']
        cmc_latest = cmc_data[0]['price']
        spread = abs(cg_latest - cmc_latest) / cmc_latest * 100
        
        metadata['cmc_validated'] = True
        metadata['spread_pct'] = spread
        
        print(f"📊 Price comparison: CG=${cg_latest:.2f} vs CMC=${cmc_latest:.2f} (spread: {spread:.2f}%)")
        
        # OPTION 1: Moyenne pondérée 70/30
        weighted_price = (cg_latest * 0.7) + (cmc_latest * 0.3)
        
        if spread > 5.0:
            print(f"⚠️  Large divergence ({spread:.2f}%) - using weighted average")
            metadata['method'] = 'weighted_average_high_spread'
        else:
            print(f"✅ Prices aligned ({spread:.2f}%) - using weighted average")
            metadata['method'] = 'weighted_average'
        
        # Appliquer le weighted price à tous les points
        # On garde la structure temporelle de CoinGecko mais ajuste les prix
        adjustment_ratio = weighted_price / cg_latest
        weighted_prices = []
        for p in cg_prices:
            weighted_prices.append({
                'timestamp': p['timestamp'],
                'price': p['price'] * adjustment_ratio
            })
        
        metadata['source'] = 'coingecko_cmc_weighted'
        return weighted_prices, metadata


    @staticmethod
    def fetch_coin_list(page: int = 1, limit: int = 50) -> Tuple[List[Dict], Dict]:
        """
        Fetch list of top cryptocurrencies from CoinGecko
        
        Args:
            page: Page number (1-indexed)
            limit: Number of coins per page
        
        Returns:
            Tuple of (coins list, metadata dict)
        """
        try:
            url = f"{DirectAPIFetcher.COINGECKO_BASE}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': page,
                'sparkline': True,
                'price_change_percentage': '1h,24h,7d'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                coins = []
                for coin in data:
                    coins.append({
                        'id': coin.get('id'),
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name'),
                        'image': coin.get('image'),
                        'current_price': coin.get('current_price'),
                        'market_cap': coin.get('market_cap'),
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'fully_diluted_valuation': coin.get('fully_diluted_valuation'),
                        'total_volume': coin.get('total_volume'),
                        'high_24h': coin.get('high_24h'),
                        'low_24h': coin.get('low_24h'),
                        'price_change_24h': coin.get('price_change_24h'),
                        'price_change_percentage_24h': coin.get('price_change_percentage_24h'),
                        'price_change_percentage_1h': coin.get('price_change_percentage_1h_in_currency'),
                        'price_change_percentage_7d': coin.get('price_change_percentage_7d_in_currency'),
                        'circulating_supply': coin.get('circulating_supply'),
                        'total_supply': coin.get('total_supply'),
                        'max_supply': coin.get('max_supply'),
                        'sparkline_in_7d': coin.get('sparkline_in_7d', {}).get('price', [])
                    })
                
                metadata = {
                    'source': 'coingecko',
                    'stale': False,
                    'rate_limited': False
                }
                
                return coins, metadata
            
            return [], {'source': 'error', 'stale': False, 'rate_limited': response.status_code == 429}
            
        except Exception as e:
            print(f"❌ Error fetching coin list: {e}")
            return [], {'source': 'error', 'stale': False, 'rate_limited': False}


    @staticmethod
    def fetch_global_stats() -> Optional[Dict]:
        """
        Fetch global cryptocurrency market statistics
        
        Returns:
            Global market data (total market cap, volume, etc.)
        """
        try:
            url = f"{DirectAPIFetcher.COINGECKO_BASE}/global"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                return {
                    'active_cryptocurrencies': data.get('active_cryptocurrencies'),
                    'markets': data.get('markets'),
                    'total_market_cap_usd': data.get('total_market_cap', {}).get('usd'),
                    'total_volume_usd': data.get('total_volume', {}).get('usd'),
                    'market_cap_percentage': data.get('market_cap_percentage', {}),
                    'market_cap_change_percentage_24h_usd': data.get('market_cap_change_percentage_24h_usd'),
                    'updated_at': datetime.fromtimestamp(data.get('updated_at', 0)).isoformat() if data.get('updated_at') else None
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching global stats: {e}")
            return None


    @staticmethod
    def fetch_fear_greed() -> Optional[Dict]:
        """
        Fetch Fear & Greed Index from Alternative.me API
        
        Returns:
            Fear & Greed index data
        """
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', [{}])[0]
                
                return {
                    'value': int(data.get('value', 50)),
                    'value_classification': data.get('value_classification', 'Neutral'),
                    'timestamp': datetime.fromtimestamp(int(data.get('timestamp', 0))).isoformat() if data.get('timestamp') else None,
                    'time_until_update': data.get('time_until_update')
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching fear/greed: {e}")
            return None
