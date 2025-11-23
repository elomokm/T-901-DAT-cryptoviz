## Runner for CoinGecko Agent
#!/usr/bin/env python3
"""Script de lancement pour l'agent CoinGecko

Permet de surcharger l'intervalle via:
- argument CLI: --interval 30
- variable d'env: COINGECKO_POLL_INTERVAL

Fallback: 30s par défaut pour la démo.
"""

import sys
import os
import argparse

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.coingecko_agent import CoinGeckoAgent
from agents.config import COINGECKO_POLL_INTERVAL as CONFIG_DEFAULT_INTERVAL


def parse_interval() -> int:
    """Calcule l'intervalle final en respectant la priorité CLI > ENV > config > 30"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--interval", "-i", type=int, help="Intervalle de polling en secondes")
    # Ne pas faire échouer si d'autres args inconnus (compat)
    args, _ = parser.parse_known_args()

    # 1) CLI
    if args.interval is not None:
        return max(5, args.interval)  # garde-fou minimal

    # 2) ENV
    env_val = os.getenv("COINGECKO_POLL_INTERVAL")
    if env_val and env_val.isdigit():
        return max(5, int(env_val))

    # 3) config.py
    if isinstance(CONFIG_DEFAULT_INTERVAL, int) and CONFIG_DEFAULT_INTERVAL > 0:
        return CONFIG_DEFAULT_INTERVAL

    # 4) fallback démo
    return 30


def main():
    """Point d'entrée du script"""
    interval = parse_interval()

    print("="*60)
    print(" CoinGecko Agent - Scraping + Validation")
    print("="*60)
    print(f"  Intervalle de polling: {interval}s")
    print()
    
    # Créer et lancer l'agent
    agent = CoinGeckoAgent(poll_interval=interval)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n Arrêt propre de l'agent")
        sys.exit(0)


if __name__ == "__main__":
    main()