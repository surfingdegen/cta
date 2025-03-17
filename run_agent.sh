#!/bin/bash
# Script to run the crypto trading agent with common options

# Default values
CONFIG_PATH="./config/config.json"
INTERVAL=60
MODE="continuous"
TOKEN=""
HOST="127.0.0.1"
PORT=5000
DEBUG=false

# Display help
function show_help {
    echo "Usage: ./run_agent.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -c, --config PATH          Specify configuration file path (default: ./config/config.json)"
    echo "  -o, --once                 Run the agent once and exit"
    echo "  -i, --interval MINUTES     Set interval in minutes between runs (default: 60)"
    echo "  -w, --wallet               Check wallet balances and exit"
    echo "  -a, --analyze TOKEN        Analyze a specific token and exit (e.g., BTC, ETH)"
    echo "  -u, --web                  Run the web interface"
    echo "  --host HOST                Host to run the web server on (default: 127.0.0.1)"
    echo "  --port PORT                Port to run the web server on (default: 5000)"
    echo "  --debug                    Run in debug mode"
    echo ""
    echo "Examples:"
    echo "  ./run_agent.sh                       # Run continuously with default settings"
    echo "  ./run_agent.sh --once                # Run once and exit"
    echo "  ./run_agent.sh --interval 30         # Run every 30 minutes"
    echo "  ./run_agent.sh --wallet              # Check wallet balances"
    echo "  ./run_agent.sh --analyze BTC         # Analyze Bitcoin"
    echo "  ./run_agent.sh --web                 # Run the web interface"
    echo "  ./run_agent.sh --web --port 8080     # Run the web interface on port 8080"
    echo ""
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -o|--once)
            MODE="once"
            shift
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        -w|--wallet)
            MODE="wallet"
            shift
            ;;
        -a|--analyze)
            MODE="analyze"
            TOKEN="$2"
            shift 2
            ;;
        -u|--web)
            MODE="web"
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if the config file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Error: Configuration file not found at $CONFIG_PATH"
    exit 1
fi

# Navigate to the src directory
cd "$(dirname "$0")"
cd src

# Run the agent with the specified options
case $MODE in
    "once")
        echo "Running agent once..."
        ./main.py --config "$CONFIG_PATH" --run-once
        ;;
    "wallet")
        echo "Checking wallet balances..."
        ./main.py --config "$CONFIG_PATH" --check-wallet
        ;;
    "analyze")
        echo "Analyzing token: $TOKEN..."
        ./main.py --config "$CONFIG_PATH" --analyze-token "$TOKEN"
        ;;
    "web")
        echo "Starting web interface on $HOST:$PORT..."
        if [ "$DEBUG" = true ]; then
            ./main.py --config "$CONFIG_PATH" --web --host "$HOST" --port "$PORT" --debug
        else
            ./main.py --config "$CONFIG_PATH" --web --host "$HOST" --port "$PORT"
        fi
        ;;
    "continuous")
        echo "Running agent continuously with interval of $INTERVAL minutes..."
        ./main.py --config "$CONFIG_PATH" --interval "$INTERVAL"
        ;;
esac
