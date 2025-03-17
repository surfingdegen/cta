#!/usr/bin/env python3
"""
Test script for the cryptocurrency trading agent.
This script tests each component of the agent to ensure they are working correctly.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

from wallet import BlockchainWallet
from technical_analysis import TechnicalAnalyzer
from sentiment_analysis import SentimentAnalyzer
from trading_strategy import TradingStrategy
from loguru import logger


def setup_logger():
    """Set up the logger for testing."""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(sys.stderr, level="INFO")


def test_wallet(config_path):
    """Test the wallet module."""
    print("\n=== Testing Wallet Module ===")
    
    try:
        wallet = BlockchainWallet(config_path)
        print("✅ Wallet initialization successful")
        
        # Test getting portfolio value
        portfolio = wallet.get_portfolio_value()
        print("✅ Portfolio retrieval successful")
        print(f"Portfolio: {json.dumps(portfolio, indent=2, default=str)}")
        
        return True
    except Exception as e:
        print(f"❌ Wallet test failed: {str(e)}")
        return False


def test_technical_analysis(config_path):
    """Test the technical analysis module."""
    print("\n=== Testing Technical Analysis Module ===")
    
    try:
        analyzer = TechnicalAnalyzer(config_path)
        print("✅ Technical analyzer initialization successful")
        
        # Generate sample price data
        import random
        import pandas as pd
        from datetime import datetime, timedelta
        
        sample_data = []
        base_price = 1000
        timestamp = pd.Timestamp.now() - pd.Timedelta(days=7)
        
        for i in range(7 * 24):  # 7 days of hourly data
            price = base_price * (1 + random.uniform(-0.02, 0.02))
            base_price = price
            
            sample_data.append({
                "timestamp": int(timestamp.timestamp() * 1000),
                "open": price * (1 - random.uniform(0, 0.005)),
                "high": price * (1 + random.uniform(0, 0.01)),
                "low": price * (1 - random.uniform(0, 0.01)),
                "close": price,
                "volume": random.uniform(10, 100)
            })
            
            timestamp += pd.Timedelta(hours=1)
        
        # Test analysis
        analysis = analyzer.analyze(sample_data)
        print("✅ Technical analysis successful")
        print(f"Analysis result: {json.dumps(analysis['signals'], indent=2, default=str)}")
        
        return True
    except Exception as e:
        print(f"❌ Technical analysis test failed: {str(e)}")
        return False


def test_sentiment_analysis(config_path):
    """Test the sentiment analysis module."""
    print("\n=== Testing Sentiment Analysis Module ===")
    
    try:
        analyzer = SentimentAnalyzer(config_path)
        print("✅ Sentiment analyzer initialization successful")
        
        # Test with a sample tweet
        sample_tweet = "I love Bitcoin! It's going to the moon! #BTC #crypto"
        score, sentiment = analyzer._get_tweet_sentiment(sample_tweet)
        print(f"✅ Sample tweet sentiment analysis: {sentiment} (score: {score})")
        
        # Note: We're not testing the actual Twitter API calls here
        # as they require valid credentials
        print("ℹ️ Twitter API calls not tested (requires valid credentials)")
        
        return True
    except Exception as e:
        print(f"❌ Sentiment analysis test failed: {str(e)}")
        return False


def test_trading_strategy(config_path):
    """Test the trading strategy module."""
    print("\n=== Testing Trading Strategy Module ===")
    
    try:
        strategy = TradingStrategy(config_path)
        print("✅ Trading strategy initialization successful")
        
        # Test with a sample token
        token = {
            "symbol": "TEST",
            "address": "0x0000000000000000000000000000000000000000",
            "chain": "ethereum",
            "min_holding": 0.1,
            "max_holding": 5.0
        }
        
        # Test position size calculation
        from decimal import Decimal
        position_size = strategy._calculate_position_size(token, Decimal("10000"))
        print(f"✅ Position size calculation: {position_size}")
        
        return True
    except Exception as e:
        print(f"❌ Trading strategy test failed: {str(e)}")
        return False


def main():
    """Main entry point for the test script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test the cryptocurrency trading agent")
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="./config/config.json",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Set up logger
    setup_logger()
    
    # Run tests
    print("Starting tests for the cryptocurrency trading agent...")
    print(f"Using configuration file: {args.config}")
    
    # Test each module
    wallet_success = test_wallet(args.config)
    technical_success = test_technical_analysis(args.config)
    sentiment_success = test_sentiment_analysis(args.config)
    strategy_success = test_trading_strategy(args.config)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Wallet Module: {'✅ Passed' if wallet_success else '❌ Failed'}")
    print(f"Technical Analysis Module: {'✅ Passed' if technical_success else '❌ Failed'}")
    print(f"Sentiment Analysis Module: {'✅ Passed' if sentiment_success else '❌ Failed'}")
    print(f"Trading Strategy Module: {'✅ Passed' if strategy_success else '❌ Failed'}")
    
    # Overall result
    if wallet_success and technical_success and sentiment_success and strategy_success:
        print("\n✅ All tests passed! The agent is ready to use.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
