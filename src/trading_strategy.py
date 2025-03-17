"""
Trading strategy module for cryptocurrency trading.
This module combines technical analysis and sentiment analysis
to make trading decisions for cryptocurrency tokens.
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from technical_analysis import TechnicalAnalyzer
from sentiment_analysis import SentimentAnalyzer
from wallet import BlockchainWallet


class TradingStrategy:
    """
    A class to implement trading strategies for cryptocurrency tokens.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the trading strategy with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Extract trading parameters from config
        self.trading_config = self.config["trading"]
        
        # Initialize parameters
        self.max_allocation = self.trading_config["max_allocation_per_trade"]
        self.stop_loss = self.trading_config["stop_loss_percentage"]
        self.take_profit = self.trading_config["take_profit_percentage"]
        self.max_slippage = self.trading_config["max_slippage"]
        
        # Initialize analyzers
        self.technical_analyzer = TechnicalAnalyzer(config_path)
        self.sentiment_analyzer = SentimentAnalyzer(config_path)
        self.wallet = BlockchainWallet(config_path)
        
        # Initialize trade history
        self.trade_history = []
        
        # Initialize active trades
        self.active_trades = {}
        
        # Load trade history if exists
        self._load_trade_history()
    
    def _load_trade_history(self):
        """Load trade history from file if it exists."""
        try:
            with open("../logs/trade_history.json", 'r') as f:
                self.trade_history = json.load(f)
            logger.info(f"Loaded {len(self.trade_history)} historical trades")
        except FileNotFoundError:
            logger.info("No trade history file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading trade history: {str(e)}")
    
    def _save_trade_history(self):
        """Save trade history to file."""
        try:
            with open("../logs/trade_history.json", 'w') as f:
                json.dump(self.trade_history, f, indent=2, default=str)
            logger.info(f"Saved {len(self.trade_history)} trades to history")
        except Exception as e:
            logger.error(f"Error saving trade history: {str(e)}")
    
    def _record_trade(self, trade_data: Dict[str, Any]):
        """
        Record a trade in the trade history.
        
        Args:
            trade_data: Dictionary containing trade details
        """
        # Add timestamp
        trade_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Add to trade history
        self.trade_history.append(trade_data)
        
        # Save trade history
        self._save_trade_history()
        
        # Log trade
        logger.info(f"Recorded trade: {trade_data['action']} {trade_data['amount']} {trade_data['token']} at {trade_data['price']}")
    
    def _calculate_position_size(self, token_data: Dict[str, Any], 
                               portfolio_value: Decimal) -> Decimal:
        """
        Calculate the position size for a trade based on portfolio value and risk.
        
        Args:
            token_data: Token data from config
            portfolio_value: Total portfolio value in USD
            
        Returns:
            Decimal: Position size in USD
        """
        # Get max allocation percentage
        max_allocation = Decimal(str(self.max_allocation))
        
        # Calculate base position size
        position_size = portfolio_value * max_allocation
        
        # Adjust based on token-specific settings if available
        min_holding = Decimal(str(token_data.get("min_holding", 0)))
        max_holding = Decimal(str(token_data.get("max_holding", float('inf'))))
        
        # Ensure position is within token-specific limits
        # This would need price data to convert between USD and token amounts
        
        return position_size
    
    def _get_price_data(self, token_symbol: str, timeframe: str = "1h", 
                      limit: int = 200) -> List[Dict[str, Any]]:
        """
        Get historical price data for a token.
        This is a placeholder that would be replaced with actual API calls.
        
        Args:
            token_symbol: The token symbol
            timeframe: The timeframe for candles (e.g., 1h, 4h, 1d)
            limit: Number of candles to retrieve
            
        Returns:
            List[Dict]: List of price data points
        """
        # In a real implementation, this would call an exchange API
        # For now, we'll generate random data for demonstration
        
        logger.info(f"Getting price data for {token_symbol} ({timeframe}, {limit} candles)")
        
        # This is just placeholder code
        import random
        
        price_data = []
        base_price = 1000 if token_symbol == "BTC" else 100  # Simplified
        timestamp = int(time.time() * 1000) - (limit * 3600 * 1000)  # Start from 'limit' hours ago
        
        for i in range(limit):
            # Generate random price movement
            price_change = random.uniform(-0.02, 0.02)
            base_price *= (1 + price_change)
            
            # Create candle data
            candle = {
                "timestamp": timestamp,
                "open": base_price * (1 - random.uniform(0, 0.005)),
                "high": base_price * (1 + random.uniform(0, 0.01)),
                "low": base_price * (1 - random.uniform(0, 0.01)),
                "close": base_price,
                "volume": random.uniform(10, 100) * base_price
            }
            
            price_data.append(candle)
            timestamp += 3600 * 1000  # Add 1 hour in milliseconds
        
        return price_data
    
    def analyze_token(self, token_symbol: str, chain: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on a token.
        
        Args:
            token_symbol: The token symbol
            chain: The blockchain where the token exists
            
        Returns:
            Dict: Analysis results
        """
        logger.info(f"Analyzing {token_symbol} on {chain}")
        
        # Get price data
        price_data = self._get_price_data(token_symbol)
        
        # Perform technical analysis
        technical_analysis = self.technical_analyzer.analyze(price_data)
        
        # Perform sentiment analysis
        sentiment_analysis = self.sentiment_analyzer.analyze_sentiment(token_symbol)
        
        # Combine analyses
        combined_analysis = {
            "token": token_symbol,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat(),
            "technical_analysis": technical_analysis,
            "sentiment_analysis": sentiment_analysis,
            "combined_signal": self._generate_combined_signal(technical_analysis, sentiment_analysis)
        }
        
        return combined_analysis
    
    def _generate_combined_signal(self, technical_analysis: Dict[str, Any], 
                                sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a combined trading signal based on technical and sentiment analysis.
        
        Args:
            technical_analysis: Technical analysis results
            sentiment_analysis: Sentiment analysis results
            
        Returns:
            Dict: Combined signal information
        """
        # Extract signals
        tech_signal = technical_analysis["signals"]["overall_signal"]
        tech_strength = technical_analysis["signals"]["signal_strength"]
        
        sentiment_score = sentiment_analysis["sentiment_score"]
        sentiment_signal = sentiment_analysis["sentiment"]
        
        # Initialize combined signal
        combined_signal = {
            "signal": "neutral",
            "strength": 0,
            "confidence": 0.5,
            "factors": []
        }
        
        # Technical analysis weight (60%)
        tech_weight = 0.6
        
        # Sentiment analysis weight (40%)
        sentiment_weight = 0.4
        
        # Calculate weighted strength
        if tech_signal == "strong_buy":
            combined_signal["strength"] += tech_weight * 100
            combined_signal["factors"].append({
                "factor": "Technical Analysis",
                "signal": "Strong Buy",
                "contribution": tech_weight * 100
            })
        elif tech_signal == "buy":
            combined_signal["strength"] += tech_weight * 50
            combined_signal["factors"].append({
                "factor": "Technical Analysis",
                "signal": "Buy",
                "contribution": tech_weight * 50
            })
        elif tech_signal == "strong_sell":
            combined_signal["strength"] -= tech_weight * 100
            combined_signal["factors"].append({
                "factor": "Technical Analysis",
                "signal": "Strong Sell",
                "contribution": -tech_weight * 100
            })
        elif tech_signal == "sell":
            combined_signal["strength"] -= tech_weight * 50
            combined_signal["factors"].append({
                "factor": "Technical Analysis",
                "signal": "Sell",
                "contribution": -tech_weight * 50
            })
        
        # Add sentiment contribution
        sentiment_contribution = sentiment_score * 100 * sentiment_weight
        combined_signal["strength"] += sentiment_contribution
        combined_signal["factors"].append({
            "factor": "Sentiment Analysis",
            "signal": sentiment_signal.capitalize(),
            "score": sentiment_score,
            "contribution": sentiment_contribution
        })
        
        # Determine overall signal
        if combined_signal["strength"] > 50:
            combined_signal["signal"] = "strong_buy"
        elif combined_signal["strength"] > 20:
            combined_signal["signal"] = "buy"
        elif combined_signal["strength"] < -50:
            combined_signal["signal"] = "strong_sell"
        elif combined_signal["strength"] < -20:
            combined_signal["signal"] = "sell"
        else:
            combined_signal["signal"] = "neutral"
        
        # Calculate confidence based on agreement between technical and sentiment
        if (tech_signal in ["buy", "strong_buy"] and sentiment_signal == "positive") or \
           (tech_signal in ["sell", "strong_sell"] and sentiment_signal == "negative"):
            combined_signal["confidence"] = 0.8
        elif tech_signal == "neutral" or sentiment_signal == "neutral":
            combined_signal["confidence"] = 0.5
        else:
            combined_signal["confidence"] = 0.3
        
        return combined_signal
    
    def execute_trade(self, token_data: Dict[str, Any], 
                     action: str, amount: Decimal) -> Dict[str, Any]:
        """
        Execute a trade based on the trading signal.
        This is a placeholder that would be replaced with actual trading logic.
        
        Args:
            token_data: Token data from config
            action: The trade action (buy, sell)
            amount: The amount to trade
            
        Returns:
            Dict: Trade result information
        """
        # In a real implementation, this would call exchange APIs or smart contracts
        # For now, we'll simulate the trade
        
        token_symbol = token_data["symbol"]
        chain = token_data["chain"]
        token_address = token_data["address"]
        
        logger.info(f"Executing {action} trade for {amount} {token_symbol} on {chain}")
        
        # Simulate trade execution
        success = True
        error = None
        
        # Get current price (simulated)
        current_price = 1000 if token_symbol == "BTC" else 100  # Simplified
        
        # Record trade details
        trade_details = {
            "token": token_symbol,
            "chain": chain,
            "action": action,
            "amount": str(amount),
            "price": current_price,
            "value_usd": float(amount) * current_price,
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Record the trade
        self._record_trade(trade_details)
        
        # Update active trades
        if action == "buy":
            self.active_trades[token_symbol] = {
                "entry_price": current_price,
                "amount": amount,
                "entry_time": datetime.utcnow().isoformat(),
                "stop_loss": current_price * (1 - self.stop_loss),
                "take_profit": current_price * (1 + self.take_profit)
            }
        elif action == "sell" and token_symbol in self.active_trades:
            del self.active_trades[token_symbol]
        
        return trade_details
    
    def check_portfolio(self) -> Dict[str, Any]:
        """
        Check the current portfolio status.
        
        Returns:
            Dict: Portfolio information
        """
        # Get portfolio from wallet
        portfolio = self.wallet.get_portfolio_value()
        
        # Add active trades information
        portfolio["active_trades"] = self.active_trades
        
        # Add trade history summary
        if self.trade_history:
            # Calculate profit/loss
            total_bought = sum(float(trade["value_usd"]) for trade in self.trade_history if trade["action"] == "buy")
            total_sold = sum(float(trade["value_usd"]) for trade in self.trade_history if trade["action"] == "sell")
            
            portfolio["trading_summary"] = {
                "total_trades": len(self.trade_history),
                "buys": sum(1 for trade in self.trade_history if trade["action"] == "buy"),
                "sells": sum(1 for trade in self.trade_history if trade["action"] == "sell"),
                "total_bought_usd": total_bought,
                "total_sold_usd": total_sold,
                "realized_pnl": total_sold - total_bought
            }
        
        return portfolio
    
    def run_strategy(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the trading strategy for a specific token.
        
        Args:
            token_data: Token data from config
            
        Returns:
            Dict: Strategy execution results
        """
        token_symbol = token_data["symbol"]
        chain = token_data["chain"]
        
        logger.info(f"Running strategy for {token_symbol} on {chain}")
        
        # Analyze the token
        analysis = self.analyze_token(token_symbol, chain)
        
        # Get the combined signal
        signal = analysis["combined_signal"]["signal"]
        strength = analysis["combined_signal"]["strength"]
        confidence = analysis["combined_signal"]["confidence"]
        
        # Check if we already have an active trade for this token
        has_active_trade = token_symbol in self.active_trades
        
        # Get portfolio value
        portfolio = self.check_portfolio()
        
        # Initialize result
        result = {
            "token": token_symbol,
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "action_taken": "none",
            "trade_details": None
        }
        
        # Execute strategy based on signal
        if signal in ["buy", "strong_buy"] and not has_active_trade and confidence > 0.6:
            # Calculate position size
            position_size = self._calculate_position_size(token_data, Decimal("10000"))  # Simplified
            
            # Execute buy trade
            trade_details = self.execute_trade(token_data, "buy", position_size)
            
            result["action_taken"] = "buy"
            result["trade_details"] = trade_details
            
        elif signal in ["sell", "strong_sell"] and has_active_trade:
            # Get active trade details
            active_trade = self.active_trades[token_symbol]
            
            # Execute sell trade
            trade_details = self.execute_trade(token_data, "sell", active_trade["amount"])
            
            result["action_taken"] = "sell"
            result["trade_details"] = trade_details
            
        # Check stop loss and take profit for active trades
        elif has_active_trade:
            active_trade = self.active_trades[token_symbol]
            current_price = 1000 if token_symbol == "BTC" else 100  # Simplified
            
            if current_price <= active_trade["stop_loss"]:
                # Execute stop loss
                trade_details = self.execute_trade(token_data, "sell", active_trade["amount"])
                
                result["action_taken"] = "stop_loss"
                result["trade_details"] = trade_details
                
            elif current_price >= active_trade["take_profit"]:
                # Execute take profit
                trade_details = self.execute_trade(token_data, "sell", active_trade["amount"])
                
                result["action_taken"] = "take_profit"
                result["trade_details"] = trade_details
        
        return result


if __name__ == "__main__":
    # Example usage
    strategy = TradingStrategy("../config/config.json")
    
    # Define a token to analyze
    token = {
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "chain": "ethereum",
        "min_holding": 0.1,
        "max_holding": 5.0
    }
    
    # Run the strategy
    result = strategy.run_strategy(token)
    
    # Print the results
    print(json.dumps(result, indent=2, default=str))
