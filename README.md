# Crypto Trading Agent

An AI-powered cryptocurrency trading agent that manages blockchain wallets and makes trading decisions based on technical analysis and sentiment from X.com (formerly Twitter).

## Features

- **Blockchain Wallet Management**: Supports Ethereum and Binance Smart Chain wallets
- **Technical Analysis**: Implements various technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
- **Sentiment Analysis**: Analyzes sentiment from X.com posts about cryptocurrencies
- **Combined Trading Strategy**: Makes trading decisions based on both technical and sentiment signals
- **Automated Trading**: Can run continuously at specified intervals
- **Portfolio Tracking**: Monitors wallet balances and trade history
- **Risk Management**: Implements stop-loss and take-profit mechanisms
- **Web Interface**: Browser-based dashboard for monitoring and controlling the agent

## Project Structure

```
crypto-trading-agent/
├── config/
│   └── config.json         # Configuration file
├── logs/                   # Log files directory
├── src/
│   ├── main.py             # Main entry point
│   ├── wallet.py           # Blockchain wallet management
│   ├── technical_analysis.py # Technical analysis module
│   ├── sentiment_analysis.py # Sentiment analysis module
│   ├── trading_strategy.py # Trading strategy implementation
│   └── web/                # Web interface
│       ├── app.py          # Flask application
│       ├── templates/      # HTML templates
│       └── static/         # Static files (CSS, JS, images)
├── .env.example            # Example environment variables
└── requirements.txt        # Python dependencies
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/surfingdegen/crypto-trading-agent.git
   cd crypto-trading-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration:
   - Copy `.env.example` to `.env` and fill in your API keys and wallet information
   - Update `config/config.json` with your trading parameters and tokens of interest

## Configuration

The agent is configured through `config/config.json`. Key configuration sections include:

- **wallet**: Blockchain wallet settings for Ethereum and Binance Smart Chain
- **exchanges**: API credentials for exchanges like Binance
- **twitter**: API credentials for X.com (Twitter)
- **trading**: Trading parameters like allocation size, stop-loss, and take-profit percentages
- **technical_analysis**: Parameters for technical indicators
- **sentiment_analysis**: Settings for sentiment analysis, including keywords and influencers to track
- **tokens_of_interest**: List of tokens to analyze and potentially trade
- **logging**: Logging configuration

## Usage

### Using the Shell Script

The easiest way to run the agent is using the provided shell script:

```
./run_agent.sh [options]
```

For example:
- Run the web interface: `./run_agent.sh --web`
- Check wallet balances: `./run_agent.sh --wallet`
- Analyze Bitcoin: `./run_agent.sh --analyze BTC`
- Run once and exit: `./run_agent.sh --once`
- Run every 30 minutes: `./run_agent.sh --interval 30`

Run `./run_agent.sh --help` to see all available options.

### Command-line Options

If you prefer to run the Python script directly:

```
python src/main.py [options]
```

Available options:
- `--config PATH`: Specify a custom configuration file path
- `--run-once`: Run the agent once and exit
- `--interval MINUTES`: Set the interval in minutes between runs (default: 60)
- `--check-wallet`: Check wallet balances and exit
- `--analyze-token SYMBOL`: Analyze a specific token and exit (e.g., BTC, ETH)
- `--web`: Run the web interface
- `--host HOST`: Host to run the web server on (default: 127.0.0.1)
- `--port PORT`: Port to run the web server on (default: 5000)
- `--debug`: Run in debug mode

## Web Interface

The agent includes a web-based dashboard for monitoring and controlling the trading agent. To start the web interface:

```
./run_agent.sh --web
```

Then open your browser and navigate to `http://localhost:5000`.

The web interface provides:
- Dashboard with portfolio overview and token analysis
- Real-time price charts and technical indicators
- Portfolio composition visualization
- Trading history and performance metrics
- Agent control (start/stop)
- Token-specific analysis and trading signals

## Security Considerations

- **NEVER** commit your `.env` file or any file containing private keys or API secrets
- Use environment variables for sensitive information
- Consider using a hardware wallet for additional security
- Start with small allocation sizes until you're confident in the agent's performance
- Regularly monitor the agent's activities and performance
- When running the web interface, keep it on localhost or secure it properly if exposing to a network

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves significant risk. Use this agent at your own risk. The authors are not responsible for any financial losses incurred from using this software.

## License

MIT License
