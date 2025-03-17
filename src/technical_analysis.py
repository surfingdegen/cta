"""
Technical analysis module for cryptocurrency trading.
This module provides functions to analyze price data and generate trading signals
based on technical indicators such as moving averages, RSI, MACD, etc.
"""

import json
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator
from loguru import logger


class TechnicalAnalyzer:
    """
    A class to perform technical analysis on cryptocurrency price data.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the technical analyzer with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Extract technical analysis parameters from config
        self.ta_config = self.config["technical_analysis"]
        
        # Initialize parameters
        self.short_ma_period = self.ta_config["short_ma_period"]
        self.long_ma_period = self.ta_config["long_ma_period"]
        self.rsi_period = self.ta_config["rsi_period"]
        self.rsi_overbought = self.ta_config["rsi_overbought"]
        self.rsi_oversold = self.ta_config["rsi_oversold"]
        self.macd_fast_period = self.ta_config["macd_fast_period"]
        self.macd_slow_period = self.ta_config["macd_slow_period"]
        self.macd_signal_period = self.ta_config["macd_signal_period"]
    
    def preprocess_data(self, price_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Preprocess raw price data into a pandas DataFrame.
        
        Args:
            price_data: List of dictionaries containing price data
                        (timestamp, open, high, low, close, volume)
            
        Returns:
            pd.DataFrame: Processed DataFrame with price data
        """
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        
        # Ensure timestamp is in datetime format
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
        
        # Ensure all required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                raise ValueError(f"Price data must contain {col} column")
        
        # Convert price columns to float
        for col in required_columns:
            df[col] = df[col].astype(float)
        
        # Sort by index (timestamp)
        df.sort_index(inplace=True)
        
        return df
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the price DataFrame.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            pd.DataFrame: DataFrame with added technical indicators
        """
        # Make a copy to avoid modifying the original
        df_with_indicators = df.copy()
        
        # Add Simple Moving Averages
        sma_short = SMAIndicator(close=df['close'], window=self.short_ma_period)
        sma_long = SMAIndicator(close=df['close'], window=self.long_ma_period)
        df_with_indicators[f'sma_{self.short_ma_period}'] = sma_short.sma_indicator()
        df_with_indicators[f'sma_{self.long_ma_period}'] = sma_long.sma_indicator()
        
        # Add Exponential Moving Averages
        ema_short = EMAIndicator(close=df['close'], window=self.short_ma_period)
        ema_long = EMAIndicator(close=df['close'], window=self.long_ma_period)
        df_with_indicators[f'ema_{self.short_ma_period}'] = ema_short.ema_indicator()
        df_with_indicators[f'ema_{self.long_ma_period}'] = ema_long.ema_indicator()
        
        # Add RSI
        rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
        df_with_indicators['rsi'] = rsi.rsi()
        
        # Add MACD
        macd = MACD(
            close=df['close'], 
            window_slow=self.macd_slow_period,
            window_fast=self.macd_fast_period,
            window_sign=self.macd_signal_period
        )
        df_with_indicators['macd'] = macd.macd()
        df_with_indicators['macd_signal'] = macd.macd_signal()
        df_with_indicators['macd_diff'] = macd.macd_diff()
        
        # Add Bollinger Bands
        bollinger = BollingerBands(close=df['close'], window=20, window_dev=2)
        df_with_indicators['bollinger_mavg'] = bollinger.bollinger_mavg()
        df_with_indicators['bollinger_high'] = bollinger.bollinger_hband()
        df_with_indicators['bollinger_low'] = bollinger.bollinger_lband()
        
        # Add On-Balance Volume
        obv = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume'])
        df_with_indicators['obv'] = obv.on_balance_volume()
        
        # Calculate price changes
        df_with_indicators['price_change'] = df['close'].pct_change()
        df_with_indicators['price_change_1d'] = df['close'].pct_change(periods=24)  # Assuming hourly data
        
        # Calculate volatility (standard deviation of returns)
        df_with_indicators['volatility'] = df['close'].pct_change().rolling(window=24).std()
        
        return df_with_indicators
    
    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on technical indicators.
        
        Args:
            df: DataFrame with price data and indicators
            
        Returns:
            Dict: Dictionary containing trading signals and their strengths
        """
        # Get the most recent data point
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else None
        
        signals = {
            "buy_signals": [],
            "sell_signals": [],
            "overall_signal": "neutral",
            "signal_strength": 0,  # -100 to 100, negative for sell, positive for buy
            "timestamp": df.index[-1].isoformat() if not df.index.empty else None
        }
        
        # Check Moving Average Crossover
        if previous is not None:
            # SMA Crossover
            sma_short_col = f'sma_{self.short_ma_period}'
            sma_long_col = f'sma_{self.long_ma_period}'
            
            if (previous[sma_short_col] <= previous[sma_long_col] and 
                latest[sma_short_col] > latest[sma_long_col]):
                signals["buy_signals"].append({
                    "indicator": "SMA Crossover",
                    "description": f"Short-term SMA ({self.short_ma_period}) crossed above long-term SMA ({self.long_ma_period})",
                    "strength": 60
                })
                signals["signal_strength"] += 60
            
            elif (previous[sma_short_col] >= previous[sma_long_col] and 
                  latest[sma_short_col] < latest[sma_long_col]):
                signals["sell_signals"].append({
                    "indicator": "SMA Crossover",
                    "description": f"Short-term SMA ({self.short_ma_period}) crossed below long-term SMA ({self.long_ma_period})",
                    "strength": 60
                })
                signals["signal_strength"] -= 60
            
            # EMA Crossover
            ema_short_col = f'ema_{self.short_ma_period}'
            ema_long_col = f'ema_{self.long_ma_period}'
            
            if (previous[ema_short_col] <= previous[ema_long_col] and 
                latest[ema_short_col] > latest[ema_long_col]):
                signals["buy_signals"].append({
                    "indicator": "EMA Crossover",
                    "description": f"Short-term EMA ({self.short_ma_period}) crossed above long-term EMA ({self.long_ma_period})",
                    "strength": 70
                })
                signals["signal_strength"] += 70
            
            elif (previous[ema_short_col] >= previous[ema_long_col] and 
                  latest[ema_short_col] < latest[ema_long_col]):
                signals["sell_signals"].append({
                    "indicator": "EMA Crossover",
                    "description": f"Short-term EMA ({self.short_ma_period}) crossed below long-term EMA ({self.long_ma_period})",
                    "strength": 70
                })
                signals["signal_strength"] -= 70
            
            # MACD Crossover
            if (previous['macd'] <= previous['macd_signal'] and 
                latest['macd'] > latest['macd_signal']):
                signals["buy_signals"].append({
                    "indicator": "MACD Crossover",
                    "description": "MACD line crossed above signal line",
                    "strength": 65
                })
                signals["signal_strength"] += 65
            
            elif (previous['macd'] >= previous['macd_signal'] and 
                  latest['macd'] < latest['macd_signal']):
                signals["sell_signals"].append({
                    "indicator": "MACD Crossover",
                    "description": "MACD line crossed below signal line",
                    "strength": 65
                })
                signals["signal_strength"] -= 65
        
        # Check RSI
        if not pd.isna(latest['rsi']):
            if latest['rsi'] < self.rsi_oversold:
                signals["buy_signals"].append({
                    "indicator": "RSI Oversold",
                    "description": f"RSI ({latest['rsi']:.2f}) is below oversold threshold ({self.rsi_oversold})",
                    "strength": 50 + (self.rsi_oversold - latest['rsi']) * 2  # Stronger signal the more oversold
                })
                signals["signal_strength"] += 50 + (self.rsi_oversold - latest['rsi']) * 2
            
            elif latest['rsi'] > self.rsi_overbought:
                signals["sell_signals"].append({
                    "indicator": "RSI Overbought",
                    "description": f"RSI ({latest['rsi']:.2f}) is above overbought threshold ({self.rsi_overbought})",
                    "strength": 50 + (latest['rsi'] - self.rsi_overbought) * 2  # Stronger signal the more overbought
                })
                signals["signal_strength"] -= 50 + (latest['rsi'] - self.rsi_overbought) * 2
        
        # Check Bollinger Bands
        if not pd.isna(latest['bollinger_high']) and not pd.isna(latest['bollinger_low']):
            if latest['close'] > latest['bollinger_high']:
                signals["sell_signals"].append({
                    "indicator": "Bollinger Band Breakout",
                    "description": "Price broke above upper Bollinger Band",
                    "strength": 40
                })
                signals["signal_strength"] -= 40
            
            elif latest['close'] < latest['bollinger_low']:
                signals["buy_signals"].append({
                    "indicator": "Bollinger Band Breakout",
                    "description": "Price broke below lower Bollinger Band",
                    "strength": 40
                })
                signals["signal_strength"] += 40
        
        # Determine overall signal
        if signals["signal_strength"] > 50:
            signals["overall_signal"] = "strong_buy"
        elif signals["signal_strength"] > 20:
            signals["overall_signal"] = "buy"
        elif signals["signal_strength"] < -50:
            signals["overall_signal"] = "strong_sell"
        elif signals["signal_strength"] < -20:
            signals["overall_signal"] = "sell"
        else:
            signals["overall_signal"] = "neutral"
        
        # Cap signal strength between -100 and 100
        signals["signal_strength"] = max(-100, min(100, signals["signal_strength"]))
        
        return signals
    
    def analyze(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze price data and generate trading signals.
        
        Args:
            price_data: List of dictionaries containing price data
            
        Returns:
            Dict: Analysis results including indicators and signals
        """
        try:
            # Preprocess data
            df = self.preprocess_data(price_data)
            
            # Add technical indicators
            df_with_indicators = self.add_indicators(df)
            
            # Generate signals
            signals = self.generate_signals(df_with_indicators)
            
            # Add latest price data
            latest = df.iloc[-1].to_dict()
            
            # Return analysis results
            return {
                "price_data": {
                    "latest": latest,
                    "change_24h": df['close'].pct_change(periods=24).iloc[-1] if len(df) > 24 else None,
                    "change_7d": df['close'].pct_change(periods=168).iloc[-1] if len(df) > 168 else None,
                },
                "indicators": {
                    "rsi": df_with_indicators['rsi'].iloc[-1],
                    "macd": df_with_indicators['macd'].iloc[-1],
                    "macd_signal": df_with_indicators['macd_signal'].iloc[-1],
                    "macd_histogram": df_with_indicators['macd_diff'].iloc[-1],
                    "sma_short": df_with_indicators[f'sma_{self.short_ma_period}'].iloc[-1],
                    "sma_long": df_with_indicators[f'sma_{self.long_ma_period}'].iloc[-1],
                    "ema_short": df_with_indicators[f'ema_{self.short_ma_period}'].iloc[-1],
                    "ema_long": df_with_indicators[f'ema_{self.long_ma_period}'].iloc[-1],
                    "bollinger_upper": df_with_indicators['bollinger_high'].iloc[-1],
                    "bollinger_middle": df_with_indicators['bollinger_mavg'].iloc[-1],
                    "bollinger_lower": df_with_indicators['bollinger_low'].iloc[-1],
                    "volatility": df_with_indicators['volatility'].iloc[-1],
                },
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {str(e)}")
            return {
                "error": str(e),
                "signals": {
                    "overall_signal": "error",
                    "signal_strength": 0,
                    "buy_signals": [],
                    "sell_signals": []
                }
            }


if __name__ == "__main__":
    # Example usage
    import random
    
    # Generate sample price data (hourly for 7 days)
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
    
    # Analyze the sample data
    analyzer = TechnicalAnalyzer("../config/config.json")
    analysis = analyzer.analyze(sample_data)
    
    # Print the results
    print(json.dumps(analysis, indent=2, default=str))
