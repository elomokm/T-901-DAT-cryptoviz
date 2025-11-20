"""
News Scraper Agent - Collecte des actualités crypto depuis RSS feeds
Scrape CoinDesk et CoinTelegraph pour obtenir les dernières news
"""
import feedparser
import time
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
try:
    # When the project root is on sys.path (typical when running from repo root)
    from agents.base_agent import BaseAgent
    from agents.config import TOPICS
except ImportError:
    # When running the file directly (python agents/coingecko_agent.py)
    # the package context may be missing; add the parent directory to sys.path
    import os
    import sys

    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    from agents.base_agent import BaseAgent
    from agents.config import KAFKA_BROKER, TOPICS

class NewsScraperAgent(BaseAgent):
    """
    Agent qui scrape les flux RSS de sites d'actualités crypto.

    Sources:
    - CoinDesk (https://www.coindesk.com/arc/outboundfeeds/rss/)
    - CoinTelegraph (https://cointelegraph.com/rss)
    """

    # URLs des flux RSS
    RSS_FEEDS = {
        'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'cointelegraph': 'https://cointelegraph.com/rss',
    }

    def __init__(self, poll_interval: int = 300):
        """
        Args:
            poll_interval: Intervalle en secondes entre chaque scraping (default: 300s = 5min)
        """
        super().__init__(
            name="NewsScraperAgent",
            topic="crypto-news",
            poll_interval=poll_interval,
            schema_file=None  # Pas de schéma Avro pour les news (format plus flexible)
        )

        # Cache pour éviter les doublons (stocke les hash des articles déjà envoyés)
        self.seen_articles = set()
        self.cache_max_size = 1000  # Limite du cache pour éviter la croissance infinie

    def _generate_article_hash(self, article: Dict) -> str:
        """
        Génère un hash unique pour un article basé sur son titre et sa date.

        Args:
            article: Dictionnaire contenant les infos de l'article

        Returns:
            str: Hash MD5 de l'article
        """
        unique_string = f"{article['title']}_{article['published_date']}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _parse_rss_feed(self, feed_url: str, source_name: str) -> List[Dict]:
        """
        Parse un flux RSS et extrait les articles.

        Args:
            feed_url: URL du flux RSS
            source_name: Nom de la source (ex: 'coindesk')

        Returns:
            Liste de dictionnaires représentant les articles
        """
        articles = []

        try:
            # Parser le flux RSS avec feedparser
            feed = feedparser.parse(feed_url)

            if feed.bozo:  # Erreur de parsing
                print(f"⚠️  [{self.name}] Erreur parsing {source_name}: {feed.bozo_exception}")
                return articles

            # Extraire les informations de chaque article
            for entry in feed.entries[:20]:  # Limiter aux 20 derniers articles
                try:
                    # Extraire la date de publication
                    published_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_date = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.updated_parsed)
                    else:
                        published_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                    # Extraire l'image si disponible
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url')

                    # Créer l'article
                    article = {
                        'title': entry.title.strip() if hasattr(entry, 'title') else 'No Title',
                        'link': entry.link.strip() if hasattr(entry, 'link') else '',
                        'published_date': published_date,
                        'source': source_name,
                        'description': entry.summary[:500] if hasattr(entry, 'summary') else '',  # Limiter à 500 chars
                        'image_url': image_url,
                        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    }

                    # Vérifier si l'article a déjà été vu (éviter doublons)
                    article_hash = self._generate_article_hash(article)
                    if article_hash not in self.seen_articles:
                        articles.append(article)
                        self.seen_articles.add(article_hash)

                        # Nettoyer le cache si trop grand
                        if len(self.seen_articles) > self.cache_max_size:
                            # Garder seulement les 500 derniers
                            self.seen_articles = set(list(self.seen_articles)[-500:])

                except Exception as e:
                    print(f"⚠️  [{self.name}] Erreur traitement article {source_name}: {e}")
                    continue

            print(f"✅ [{self.name}] {len(articles)} nouveaux articles de {source_name}")

        except Exception as e:
            print(f"❌ [{self.name}] Erreur scraping {source_name}: {e}")

        return articles

    def fetch_data(self) -> Optional[List[Dict]]:
        """
        Collecte les articles de tous les flux RSS configurés.

        Returns:
            Liste d'articles (ou None si aucun article)
        """
        all_articles = []

        print(f"\n [{self.name}] Scraping des flux RSS...")

        # Scraper chaque source
        for source_name, feed_url in self.RSS_FEEDS.items():
            articles = self._parse_rss_feed(feed_url, source_name)
            all_articles.extend(articles)

        if all_articles:
            print(f" [{self.name}] Total: {len(all_articles)} nouveaux articles collectés")
            return all_articles
        else:
            print(f"  [{self.name}] Aucun nouvel article")
            return None

    def run(self):
        """
        Boucle principale : collecte les news et les envoie à Kafka en batch.
        Override de la méthode BaseAgent.run() pour gérer les batches.
        """
        self.connect_kafka()

        print(f" [{self.name}] Démarrage (intervalle: {self.poll_interval}s)")
        print(f" [{self.name}] Sources: {', '.join(self.RSS_FEEDS.keys())}")

        try:
            while True:
                try:
                    # Collecter les articles
                    articles = self.fetch_data()

                    # Envoyer en batch à Kafka
                    if articles:
                        stats = self.send_batch_to_kafka(
                            articles,
                            debug=True,
                            validate=False  # Pas de validation Avro pour les news
                        )
                        print(f"✅ [{self.name}] Envoyé: {stats['success']}/{len(articles)} articles en {stats['duration_ms']}ms")

                    # Attendre avant la prochaine collecte
                    print(f"⏳ [{self.name}] Prochaine collecte dans {self.poll_interval}s...")
                    time.sleep(self.poll_interval)

                except KeyboardInterrupt:
                    print(f"\n🛑 [{self.name}] Arrêt demandé")
                    break
                except Exception as e:
                    print(f"❌ [{self.name}] Erreur: {e}")
                    print(f"⏳ [{self.name}] Réessai dans 30s...")
                    time.sleep(30)  # Attendre 30s avant de réessayer en cas d'erreur

        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                print(f" [{self.name}] Déconnecté de Kafka")


if __name__ == "__main__":
    """
    Script pour tester l'agent en standalone.
    Usage: python -m agents.news_scraper_agent
    """
    import os
    from dotenv import load_dotenv

    # Charger les variables d'environnement
    load_dotenv()

    # Créer et lancer l'agent (scrape toutes les 5 minutes)
    poll_interval = int(os.getenv('NEWS_POLL_INTERVAL', 300))
    agent = NewsScraperAgent(poll_interval=poll_interval)

    print("=" * 60)
    print("  NEWS SCRAPER AGENT - Crypto News Feed Collector")
    print("=" * 60)

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n Arrêt du News Scraper Agent")
