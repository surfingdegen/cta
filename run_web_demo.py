#!/usr/bin/env python3
"""
Simplified web interface demo for the cryptocurrency trading agent.
This script runs a Flask server that serves the web interface without requiring all dependencies.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'src/web/templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'src/web/static'))

# Sample data for demo
SAMPLE_DATA = {
    'portfolio': {
        'chains': {
            'ethereum': {
                'native_balance': '1.5',
                'tokens': {
                    'USDT': {'balance': '1000.0'},
                    'LINK': {'balance': '100.0'},
                    'UNI': {'balance': '50.0'}
                }
            },
            'binance_smart_chain': {
                'native_balance': '10.0',
                'tokens': {
                    'CAKE': {'balance': '200.0'},
                    'BUSD': {'balance': '2000.0'}
                }
            }
        },
        'active_trades': {
            'BTC': {
                'entry_price': 60000.0,
                'amount': 0.1,
                'stop_loss': 57000.0,
                'take_profit': 66000.0,
                'entry_time': datetime.utcnow().isoformat()
            },
            'ETH': {
                'entry_price': 3000.0,
                'amount': 1.0,
                'stop_loss': 2850.0,
                'take_profit': 3300.0,
                'entry_time': datetime.utcnow().isoformat()
            }
        }
    },
    'analysis': {
        'BTC': {
            'analysis': {
                'technical_analysis': {
                    'price_data': {
                        'latest': {'close': 60000.0},
                        'change_24h': 0.05
                    },
                    'signals': {
                        'overall_signal': 'buy',
                        'signal_strength': 7
                    },
                    'indicators': {
                        'rsi': 65,
                        'macd': 100.5,
                        'macd_signal': 90.2,
                        'sma_short': 59500,
                        'sma_long': 58000
                    }
                },
                'sentiment_analysis': {
                    'sentiment': 'positive',
                    'sentiment_score': 0.75,
                    'tweet_count': 1250,
                    'positive_percentage': 65,
                    'neutral_percentage': 25,
                    'negative_percentage': 10
                },
                'combined_signal': {
                    'signal': 'buy',
                    'strength': 8
                }
            },
            'action_taken': 'buy'
        },
        'ETH': {
            'analysis': {
                'technical_analysis': {
                    'price_data': {
                        'latest': {'close': 3000.0},
                        'change_24h': 0.03
                    },
                    'signals': {
                        'overall_signal': 'buy',
                        'signal_strength': 6
                    },
                    'indicators': {
                        'rsi': 60,
                        'macd': 50.5,
                        'macd_signal': 45.2,
                        'sma_short': 2950,
                        'sma_long': 2900
                    }
                },
                'sentiment_analysis': {
                    'sentiment': 'positive',
                    'sentiment_score': 0.65,
                    'tweet_count': 950,
                    'positive_percentage': 60,
                    'neutral_percentage': 30,
                    'negative_percentage': 10
                },
                'combined_signal': {
                    'signal': 'buy',
                    'strength': 7
                }
            },
            'action_taken': 'buy'
        }
    },
    'config': {
        'logging': {
            'level': 'INFO',
            'rotation': '1 day',
            'retention': '1 month'
        },
        'wallet': {
            'ethereum': {
                'address': '0x1234567890abcdef1234567890abcdef12345678',
                'provider_url': 'https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'
            },
            'binance_smart_chain': {
                'address': '0x1234567890abcdef1234567890abcdef12345678',
                'provider_url': 'https://bsc-dataseed.binance.org/'
            }
        },
        'trading': {
            'max_allocation_per_trade': 0.1,
            'stop_loss_percentage': 0.05,
            'take_profit_percentage': 0.15,
            'max_slippage': 0.01,
            'gas_price_multiplier': 1.1
        },
        'tokens_of_interest': [
            {
                'symbol': 'BTC',
                'chain': 'ethereum',
                'address': '',
                'min_holding': 0.1,
                'max_holding': 5.0
            },
            {
                'symbol': 'ETH',
                'chain': 'ethereum',
                'address': '',
                'min_holding': 1.0,
                'max_holding': 10.0
            },
            {
                'symbol': 'LINK',
                'chain': 'ethereum',
                'address': '0x514910771af9ca656af840dff83e8264ecf986ca',
                'min_holding': 10.0,
                'max_holding': 100.0
            }
        ]
    }
}


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')


@app.route('/portfolio')
def portfolio():
    """Render the portfolio page."""
    return render_template('portfolio.html')


@app.route('/analysis')
def analysis():
    """Render the analysis page."""
    return render_template('analysis.html')


@app.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html')


@app.route('/api/status', methods=['GET'])
def api_status():
    """API endpoint to get the current status of the agent."""
    return jsonify({
        'agent_running': True,
        'last_update': datetime.utcnow().isoformat(),
        'portfolio_available': True,
        'analysis_available': True,
        'tokens_analyzed': list(SAMPLE_DATA['analysis'].keys())
    })


@app.route('/api/portfolio', methods=['GET'])
def api_portfolio():
    """API endpoint to get portfolio data."""
    return jsonify(SAMPLE_DATA['portfolio'])


@app.route('/api/analysis/<token>', methods=['GET'])
def api_analysis(token):
    """API endpoint to get analysis data for a specific token."""
    if token in SAMPLE_DATA['analysis']:
        return jsonify(SAMPLE_DATA['analysis'][token])
    else:
        return jsonify({'status': 'error', 'message': f'Analysis for {token} not available'})


@app.route('/api/config', methods=['GET'])
def api_config():
    """API endpoint to get the current configuration."""
    return jsonify(SAMPLE_DATA['config'])


@app.route('/api/chart/<token>', methods=['GET'])
def api_chart(token):
    """API endpoint to get a price chart for a token."""
    # Return a dummy chart
    return jsonify({'chart': '{}'})


if __name__ == '__main__':
    print("Starting web demo on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
