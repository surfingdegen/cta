"""
Flask application for the cryptocurrency trading agent web interface.
"""

import os
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

from ..wallet import BlockchainWallet
from ..technical_analysis import TechnicalAnalyzer
from ..sentiment_analysis import SentimentAnalyzer
from ..trading_strategy import TradingStrategy


# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

# Global variables
config_path = None
trading_agent = None
agent_thread = None
agent_running = False
last_update = None
portfolio_data = None
analysis_results = {}


def initialize_agent(config_path: str):
    """Initialize the trading agent components."""
    global trading_agent
    
    if trading_agent is None:
        trading_agent = {
            'wallet': BlockchainWallet(config_path),
            'technical_analyzer': TechnicalAnalyzer(config_path),
            'sentiment_analyzer': SentimentAnalyzer(config_path),
            'trading_strategy': TradingStrategy(config_path),
            'config_path': config_path
        }
        
        # Load configuration
        with open(config_path, 'r') as f:
            trading_agent['config'] = json.load(f)


def agent_worker(interval: int = 60):
    """Background worker to run the trading agent."""
    global agent_running, last_update, portfolio_data, analysis_results
    
    while agent_running:
        try:
            # Update portfolio data
            portfolio_data = trading_agent['wallet'].get_portfolio_value()
            
            # Analyze tokens
            for token in trading_agent['config']['tokens_of_interest']:
                symbol = token['symbol']
                chain = token['chain']
                
                # Run strategy for the token
                result = trading_agent['trading_strategy'].run_strategy(token)
                
                # Store result
                analysis_results[symbol] = result
                
                # Emit update via Socket.IO
                socketio.emit('agent_update', {
                    'timestamp': datetime.utcnow().isoformat(),
                    'portfolio': portfolio_data,
                    'analysis': analysis_results
                })
                
                # Add a delay to avoid rate limiting
                time.sleep(1)
            
            # Update last update time
            last_update = datetime.utcnow()
            
            # Sleep for the specified interval
            time.sleep(interval)
            
        except Exception as e:
            print(f"Error in agent worker: {str(e)}")
            time.sleep(10)  # Sleep for a bit before retrying


def start_agent_thread(interval: int = 60):
    """Start the agent in a background thread."""
    global agent_thread, agent_running
    
    if agent_thread is None or not agent_thread.is_alive():
        agent_running = True
        agent_thread = threading.Thread(target=agent_worker, args=(interval,))
        agent_thread.daemon = True
        agent_thread.start()


def stop_agent_thread():
    """Stop the agent background thread."""
    global agent_running
    agent_running = False


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html', 
                          portfolio=portfolio_data,
                          analysis=analysis_results,
                          last_update=last_update,
                          agent_running=agent_running)


@app.route('/portfolio')
def portfolio():
    """Render the portfolio page."""
    return render_template('portfolio.html', 
                          portfolio=portfolio_data,
                          last_update=last_update)


@app.route('/analysis')
def analysis():
    """Render the analysis page."""
    return render_template('analysis.html', 
                          analysis=analysis_results,
                          last_update=last_update)


@app.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html', 
                          config=trading_agent['config'] if trading_agent else None)


@app.route('/api/start', methods=['POST'])
def api_start():
    """API endpoint to start the trading agent."""
    global agent_running
    
    interval = request.json.get('interval', 60)
    
    if not agent_running:
        start_agent_thread(interval)
        return jsonify({'status': 'success', 'message': 'Agent started'})
    else:
        return jsonify({'status': 'error', 'message': 'Agent already running'})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """API endpoint to stop the trading agent."""
    global agent_running
    
    if agent_running:
        stop_agent_thread()
        return jsonify({'status': 'success', 'message': 'Agent stopped'})
    else:
        return jsonify({'status': 'error', 'message': 'Agent not running'})


@app.route('/api/portfolio', methods=['GET'])
def api_portfolio():
    """API endpoint to get portfolio data."""
    if portfolio_data:
        return jsonify(portfolio_data)
    else:
        return jsonify({'status': 'error', 'message': 'Portfolio data not available'})


@app.route('/api/analysis/<token>', methods=['GET'])
def api_analysis(token):
    """API endpoint to get analysis data for a specific token."""
    if token in analysis_results:
        return jsonify(analysis_results[token])
    else:
        return jsonify({'status': 'error', 'message': f'Analysis for {token} not available'})


@app.route('/api/analyze/<token>', methods=['POST'])
def api_analyze_token(token):
    """API endpoint to analyze a specific token on demand."""
    # Find the token in the configuration
    token_config = None
    for t in trading_agent['config']['tokens_of_interest']:
        if t['symbol'].lower() == token.lower():
            token_config = t
            break
    
    if token_config:
        # Analyze the token
        result = trading_agent['trading_strategy'].run_strategy(token_config)
        
        # Store result
        analysis_results[token_config['symbol']] = result
        
        return jsonify(result)
    else:
        return jsonify({'status': 'error', 'message': f'Token {token} not found in configuration'})


def create_price_chart(token_symbol: str, price_data: list) -> str:
    """Create a price chart for a token."""
    # Convert price data to a format suitable for plotting
    dates = [datetime.fromtimestamp(d['timestamp'] / 1000) for d in price_data]
    closes = [d['close'] for d in price_data]
    
    # Create figure
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=dates,
        y=closes,
        mode='lines',
        name=f'{token_symbol} Price',
        line=dict(color='blue', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{token_symbol} Price Chart',
        xaxis_title='Date',
        yaxis_title='Price',
        template='plotly_white',
        height=500
    )
    
    # Convert to JSON
    return json.dumps(fig, cls=PlotlyJSONEncoder)


@app.route('/api/chart/<token>', methods=['GET'])
def api_chart(token):
    """API endpoint to get a price chart for a token."""
    if token in analysis_results:
        # Get price data from the trading strategy
        price_data = trading_agent['trading_strategy']._get_price_data(token)
        
        # Create chart
        chart_json = create_price_chart(token, price_data)
        
        return jsonify({'chart': chart_json})
    else:
        return jsonify({'status': 'error', 'message': f'Data for {token} not available'})


@app.route('/api/config', methods=['GET'])
def api_config():
    """API endpoint to get the current configuration."""
    if trading_agent and 'config' in trading_agent:
        # Remove sensitive information
        config_copy = trading_agent['config'].copy()
        if 'wallet' in config_copy:
            for chain in config_copy['wallet']:
                if 'private_key' in config_copy['wallet'][chain]:
                    config_copy['wallet'][chain]['private_key'] = '***'
        
        if 'exchanges' in config_copy:
            for exchange in config_copy['exchanges']:
                if 'api_secret' in config_copy['exchanges'][exchange]:
                    config_copy['exchanges'][exchange]['api_secret'] = '***'
        
        if 'twitter' in config_copy:
            for key in ['api_secret', 'access_token_secret', 'bearer_token']:
                if key in config_copy['twitter']:
                    config_copy['twitter'][key] = '***'
        
        return jsonify(config_copy)
    else:
        return jsonify({'status': 'error', 'message': 'Configuration not available'})


@app.route('/api/status', methods=['GET'])
def api_status():
    """API endpoint to get the current status of the agent."""
    return jsonify({
        'agent_running': agent_running,
        'last_update': last_update.isoformat() if last_update else None,
        'portfolio_available': portfolio_data is not None,
        'analysis_available': len(analysis_results) > 0,
        'tokens_analyzed': list(analysis_results.keys())
    })


def run_web_server(config_path: str, host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """Run the Flask web server."""
    global app
    
    # Initialize the trading agent
    initialize_agent(config_path)
    
    # Start the web server
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the trading agent web interface")
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="../config/config.json",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the web server on"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the web server on"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the web server in debug mode"
    )
    
    args = parser.parse_args()
    
    # Run the web server
    run_web_server(args.config, args.host, args.port, args.debug)
