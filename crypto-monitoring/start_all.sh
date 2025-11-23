#!/bin/bash

###############################################################################
# CryptoViz - Start All Components
# Lance tous les agents (producers) et consumers dans des terminaux séparés
###############################################################################

set -e

echo "============================================================================"
echo "🚀 CryptoViz - Starting All Components"
echo "============================================================================"
echo ""

# Couleurs pour output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérifier que Docker Compose est lancé
echo -e "${BLUE}📦 Checking Docker services...${NC}"
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Docker services not running. Starting them...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ Waiting 30s for services to be ready...${NC}"
    sleep 30
else
    echo -e "${GREEN}✅ Docker services already running${NC}"
fi

echo ""
echo -e "${BLUE}📊 Services Status:${NC}"
docker-compose ps

echo ""
echo "============================================================================"
echo -e "${BLUE}🎯 Starting Producers (Market Data Feed Collectors)${NC}"
echo "============================================================================"

# Démarrer les agents dans des terminaux séparés (selon OS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - utiliser Terminal.app
    echo -e "${GREEN}🍎 Detected macOS - launching in separate Terminal windows${NC}"

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"🟢 CoinGecko Agent\" && python run_coingecko_agent.py"
    end tell'

    sleep 1

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"🔵 CoinMarketCap Agent\" && python run_coinmarketcap_agent.py"
    end tell'

    sleep 1

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"📰 News Scraper Agent\" && python run_news_scraper.py"
    end tell'

    sleep 1

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"😨 Fear & Greed Agent\" && python run_fear_greed_agent.py"
    end tell'

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - utiliser gnome-terminal ou xterm
    echo -e "${GREEN}🐧 Detected Linux - launching in separate terminals${NC}"

    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '🟢 CoinGecko Agent' && python run_coingecko_agent.py; exec bash"
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '🔵 CoinMarketCap Agent' && python run_coinmarketcap_agent.py; exec bash"
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '📰 News Scraper Agent' && python run_news_scraper.py; exec bash"
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '😨 Fear & Greed Agent' && python run_fear_greed_agent.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd $(pwd) && source .venv/bin/activate && python run_coingecko_agent.py" &
        xterm -e "cd $(pwd) && source .venv/bin/activate && python run_coinmarketcap_agent.py" &
        xterm -e "cd $(pwd) && source .venv/bin/activate && python run_news_scraper.py" &
        xterm -e "cd $(pwd) && source .venv/bin/activate && python run_fear_greed_agent.py" &
    else
        echo -e "${YELLOW}⚠️  No terminal emulator found. Please run agents manually.${NC}"
    fi
fi

sleep 2

echo ""
echo "============================================================================"
echo -e "${BLUE}⚙️  Starting Consumers (Analytics Builders)${NC}"
echo "============================================================================"

if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"💾 Price Data Consumer\" && python consumer_prices.py"
    end tell'

    sleep 1

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"📰 News Consumer\" && python consumer_news.py"
    end tell'

    sleep 1

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"📊 Analytics Consumer\" && python consumer_analytics.py"
    end tell'

    sleep 1

    osascript -e 'tell application "Terminal"
        do script "cd \"'"$(pwd)"'\" && source .venv/bin/activate && echo \"🚨 Anomaly Detection Consumer\" && python consumer_anomaly_detection.py"
    end tell'

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '💾 Price Data Consumer' && python consumer_prices.py; exec bash"
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '📰 News Consumer' && python consumer_news.py; exec bash"
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '📊 Analytics Consumer' && python consumer_analytics.py; exec bash"
        gnome-terminal -- bash -c "cd $(pwd) && source .venv/bin/activate && echo '🚨 Anomaly Detection Consumer' && python consumer_anomaly_detection.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd $(pwd) && source .venv/bin/activate && python consumer_prices.py" &
        xterm -e "cd $(pwd) && source .venv/bin/activate && python consumer_news.py" &
        xterm -e "cd $(pwd) && source .venv/bin/activate && python consumer_analytics.py" &
        xterm -e "cd $(pwd) && source .venv/bin/activate && python consumer_anomaly_detection.py" &
    fi
fi

sleep 2

echo ""
echo "============================================================================"
echo -e "${GREEN}✅ All components started!${NC}"
echo "============================================================================"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  ✅ Docker services (Kafka, InfluxDB, Grafana)"
echo "  ✅ 4 Producers (CoinGecko, CoinMarketCap, News, Fear&Greed)"
echo "  ✅ 4 Consumers (Prices, News, Analytics, Anomalies)"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "  • InfluxDB UI:  http://localhost:8086"
echo "  • Grafana:      http://localhost:3000 (admin/admin)"
echo "  • Kafka:        localhost:9092"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "  1. Wait 1-2 minutes for data collection"
echo "  2. Start the web app:"
echo "     cd ../crypto-app/api && uvicorn app.main:app --reload"
echo "     cd ../crypto-app/web && npm run dev"
echo "  3. Open http://localhost:3001"
echo ""
echo -e "${BLUE}🛑 To stop all components:${NC}"
echo "  • Close all terminal windows"
echo "  • Run: docker-compose down"
echo ""
echo "============================================================================"
