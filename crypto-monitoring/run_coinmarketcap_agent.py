#!/usr/bin/env python3
"""Script de lancement pour l'agent CoinMarketCap"""
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coinmarketcap_agent import CoinMarketCapAgent
from agents.config import COINMARKETCAP_POLL_INTERVAL

def main():
    """Point d'entrée du script"""
    print("="*60)
    print("🚀 CoinMarketCap Agent - Source Alternative + Validation")
    print("="*60)
    
    # Vérifier que la clé API est configurée
    from agents.config import CMC_API_KEY
    if not CMC_API_KEY:
        print("❌ ERREUR: CMC_API_KEY non définie dans .env")
        print("\n📝 Obtenez votre clé API gratuite sur:")
        print("   https://coinmarketcap.com/api/")
        print("\n💡 Ajoutez ensuite dans .env:")
        print("   CMC_API_KEY=votre_cle_ici")
        sys.exit(1)
    
    print(f"✅ CMC_API_KEY configurée: {CMC_API_KEY[:8]}...{CMC_API_KEY[-4:]}")
    print(f"⏱️  Intervalle de polling: {COINMARKETCAP_POLL_INTERVAL}s")
    print()
    
    # Créer et lancer l'agent
    agent = CoinMarketCapAgent(poll_interval=COINMARKETCAP_POLL_INTERVAL)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Arrêt propre de l'agent")
        sys.exit(0)

if __name__ == "__main__":
    main()
