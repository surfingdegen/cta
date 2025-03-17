#!/usr/bin/env python3
"""
Main entry point for the cryptocurrency trading agent.
This module ties together all components and provides a command-line interface.
"""

import os
import sys
import json
import time
import argparse
import schedule
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv

from wallet import BlockchainWallet
from technical_analysis import TechnicalAnalyzer
from sentiment_analysis import SentimentAnalyzer
from trading_strategy import TradingStrategy


# Configure logger
def setup_logger(log_level: str = "INFO"):
    """
    Set up the logger with the specified log level.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(sys.stderr, level=log_level)
    
    # Add file logger
    log_dir = Path("../logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"trading_agent_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        log_file,
        level=log_level,
        rotation="1 day",
        retention="1 month",
        compression="zip"
    )
    
    logger.info(f"Logger initialized with level {log_level}")


class CryptoTradingAgent:
    """
    Main class for the cryptocurrency trading agent.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the trading agent with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.wallet = BlockchainWallet(config_path)
        self.technical_analyzer = TechnicalAnalyzer(config_path)
        self.sentiment_analyzer = SentimentAnalyzer(config_path)
        self.trading_strategy = TradingStrategy(config_path)
        
        # Set up logger
        log_level = self.config["logging"]["level"]
        setup_logger(log_level)
        
        logger.info("Crypto Trading Agent initialized")
    
    def check_wallet_balances(self):
        """Check and log wallet balances."""
        logger.info("Checking wallet balances...")
        
        # Get portfolio
        portfolio = self.wallet.get_portfolio_value()
        
        # Log balances
        for chain, chain_data in portfolio["chains"].items():
            logger.info(f"{chain} native balance: {chain_data['native_balance']}")
            
            for token_symbol, token_data in chain_data["tokens"].items():
                logger.info(f"{chain} {token_symbol} balance: {token_data['balance']}")
        
        return portfolio
    
    def analyze_all_tokens(self):
        """Analyze all tokens of interest from the configuration."""
        logger.info("Analyzing all tokens of interest...")
        
        results = {}
        
        for token in self.config["tokens_of_interest"]:
            symbol = token["symbol"]
            chain = token["chain"]
            
            logger.info(f"Analyzing {symbol} on {chain}...")
            
            # Run strategy for the token
            result = self.trading_strategy.run_strategy(token)
            
            # Store result
            results[symbol] = result
            
            # Log result
            action = result["action_taken"]
            if action != "none":
                logger.info(f"Action taken for {symbol}: {action}")
                if result["trade_details"]:
                    logger.info(f"Trade details: {result['trade_details']}")
            else:
                logger.info(f"No action taken for {symbol}")
            
            # Add a delay to avoid rate limiting
            time.sleep(1)
        
        return results
    
    def run_once(self):
        """Run the trading agent once for all tokens of interest."""
        logger.info("Running trading agent...")
        
        # Check wallet balances
        portfolio = self.check_wallet_balances()
        
        # Analyze and trade all tokens
        results = self.analyze_all_tokens()
        
        # Check portfolio after trading
        updated_portfolio = self.trading_strategy.check_portfolio()
        
        # Return results
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_before": portfolio,
            "portfolio_after": updated_portfolio,
            "analysis_results": results
        }
    
    def schedule_runs(self, interval_minutes: int = 60):
        """
        Schedule the trading agent to run at regular intervals.
        
        Args:
            interval_minutes: Interval in minutes between runs
        """
        logger.info(f"Scheduling trading agent to run every {interval_minutes} minutes")
        
        # Schedule the first run
        schedule.every(interval_minutes).minutes.do(self.run_once)
        
        # Run immediately once
        self.run_once()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def run_web_interface(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """
        Run the web interface for the trading agent.
        
        Args:
            host: Host to run the web server on
            port: Port to run the web server on
            debug: Whether to run in debug mode
        """
        logger.info(f"Starting web interface on {host}:{port}")
        
        try:
            # Import web module
            from web.app import run_web_server
            
            # Run web server
            run_web_server(
                config_path=self.config.get("config_path", "../config/config.json"),
                host=host,
                port=port,
                debug=debug
            )
        except ImportError as e:
            logger.error(f"Error importing web module: {str(e)}")
            logger.error("Make sure the web module is installed and in the Python path")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error running web interface: {str(e)}")
            sys.exit(1)


def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Cryptocurrency Trading Agent")
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="../config/config.json",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the agent once and exit"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in minutes between runs when running continuously"
    )
    
    parser.add_argument(
        "--check-wallet",
        action="store_true",
        help="Check wallet balances and exit"
    )
    
    parser.add_argument(
        "--analyze-token",
        type=str,
        help="Analyze a specific token and exit (e.g., BTC, ETH)"
    )
    
    parser.add_argument(
        "--web",
        action="store_true",
        help="Run the web interface"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the web server on (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the web server on (default: 5000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode"
    )
    
    args = parser.parse_args()
    
    # Initialize the trading agent
    agent = CryptoTradingAgent(args.config)
    
    # Execute the requested action
    if args.web:
        # Run the web interface
        agent.run_web_interface(args.host, args.port, args.debug)
    elif args.check_wallet:
        # Check wallet balances
        agent.check_wallet_balances()
    elif args.analyze_token:
        # Find the token in the configuration
        token_config = None
        for token in agent.config["tokens_of_interest"]:
            if token["symbol"].lower() == args.analyze_token.lower():
                token_config = token
                break
        
        if token_config:
            # Analyze the token
            result = agent.trading_strategy.run_strategy(token_config)
            print(json.dumps(result, indent=2, default=str))
        else:
            logger.error(f"Token {args.analyze_token} not found in configuration")
    elif args.run_once:
        # Run the agent once
        result = agent.run_once()
        print(json.dumps(result, indent=2, default=str))
    else:
        # Run the agent continuously
        agent.schedule_runs(args.interval)


if __name__ == "__main__":
    main()
