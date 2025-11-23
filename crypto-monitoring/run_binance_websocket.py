"""Script pour lancer l'agent Binance WebSocket"""
import logging
from agents.binance_websocket_agent import BinanceWebSocketAgent

if __name__ == "__main__":
    # Configure le logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Créer l'agent (batch toutes les 5s)
    agent = BinanceWebSocketAgent(batch_interval=5)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
