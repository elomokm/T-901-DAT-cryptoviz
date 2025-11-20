#!/usr/bin/env python3
"""
Runner for Fear & Greed Agent
Collects the Fear & Greed Index and sends to Kafka
"""
import os
import sys
from dotenv import load_dotenv

# Load env
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.fear_greed_agent import FearGreedAgent


def main():
    """Launch Fear & Greed Agent"""

    print("=" * 70)
    print("📊 FEAR & GREED AGENT - Market Sentiment Collector")
    print("=" * 70)
    print()
    print("📡 Source: Alternative.me API")
    print(f"📤 Kafka Topic: crypto-market-sentiment")
    print(f"📍 Broker: {os.getenv('KAFKA_BROKER', 'localhost:9092')}")
    print()

    # Get poll interval from env (default: 300s = 5min)
    poll_interval = int(os.getenv('FEAR_GREED_POLL_INTERVAL', 300))
    print(f"⏱️  Poll interval: {poll_interval}s ({poll_interval//60}min)")
    print()
    print("=" * 70)
    print()

    # Create and run agent
    agent = FearGreedAgent(poll_interval=poll_interval)

    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Stopping Fear & Greed Agent")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
