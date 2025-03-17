"""
Wallet module for managing blockchain wallet operations.
This module handles interactions with Ethereum and Binance Smart Chain wallets,
including checking balances, sending transactions, and approving token transfers.
"""

import json
import os
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

from web3 import Web3
from web3.middleware import geth_poa_middleware
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Standard ERC20 ABI for token interactions
ERC20_ABI = json.loads('''
[
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]
''')

class BlockchainWallet:
    """
    A class to manage blockchain wallet operations across different chains.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the wallet with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.wallets = {}
        self.web3_connections = {}
        
        # Initialize connections to different blockchains
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize Web3 connections to configured blockchains."""
        # Ethereum connection
        if "ethereum" in self.config["wallet"]:
            eth_config = self.config["wallet"]["ethereum"]
            eth_provider = Web3.HTTPProvider(eth_config["provider_url"])
            eth_w3 = Web3(eth_provider)
            
            # Use private key from environment variable if available
            private_key = os.getenv("ETH_PRIVATE_KEY", eth_config["private_key"])
            
            self.web3_connections["ethereum"] = eth_w3
            self.wallets["ethereum"] = {
                "address": eth_config["address"],
                "private_key": private_key
            }
            
            logger.info(f"Initialized Ethereum wallet: {eth_config['address']}")
        
        # Binance Smart Chain connection
        if "binance_smart_chain" in self.config["wallet"]:
            bsc_config = self.config["wallet"]["binance_smart_chain"]
            bsc_provider = Web3.HTTPProvider(bsc_config["provider_url"])
            bsc_w3 = Web3(bsc_provider)
            
            # BSC uses PoA consensus, so we need this middleware
            bsc_w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Use private key from environment variable if available
            private_key = os.getenv("BSC_PRIVATE_KEY", bsc_config["private_key"])
            
            self.web3_connections["binance_smart_chain"] = bsc_w3
            self.wallets["binance_smart_chain"] = {
                "address": bsc_config["address"],
                "private_key": private_key
            }
            
            logger.info(f"Initialized Binance Smart Chain wallet: {bsc_config['address']}")
    
    def get_native_balance(self, chain: str) -> Decimal:
        """
        Get the native token balance (ETH, BNB, etc.) for the specified chain.
        
        Args:
            chain: The blockchain to check (ethereum, binance_smart_chain)
            
        Returns:
            Decimal: The balance in the native token
        """
        if chain not in self.web3_connections:
            logger.error(f"Chain {chain} not configured")
            return Decimal('0')
        
        w3 = self.web3_connections[chain]
        address = self.wallets[chain]["address"]
        
        wei_balance = w3.eth.get_balance(address)
        eth_balance = w3.from_wei(wei_balance, 'ether')
        
        logger.info(f"Native balance on {chain}: {eth_balance}")
        return Decimal(str(eth_balance))
    
    def get_token_balance(self, chain: str, token_address: str) -> Tuple[Decimal, int]:
        """
        Get the balance of a specific token.
        
        Args:
            chain: The blockchain where the token exists
            token_address: The contract address of the token
            
        Returns:
            Tuple[Decimal, int]: The balance and token decimals
        """
        if chain not in self.web3_connections:
            logger.error(f"Chain {chain} not configured")
            return Decimal('0'), 18
        
        w3 = self.web3_connections[chain]
        wallet_address = self.wallets[chain]["address"]
        
        # Create contract instance
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Get token decimals
        decimals = token_contract.functions.decimals().call()
        
        # Get raw balance
        raw_balance = token_contract.functions.balanceOf(wallet_address).call()
        
        # Convert to decimal
        token_balance = Decimal(raw_balance) / Decimal(10 ** decimals)
        
        # Get token symbol
        try:
            symbol = token_contract.functions.symbol().call()
            logger.info(f"Token balance for {symbol} on {chain}: {token_balance}")
        except Exception:
            logger.info(f"Token balance for {token_address} on {chain}: {token_balance}")
        
        return token_balance, decimals
    
    def approve_token_spending(self, chain: str, token_address: str, spender_address: str, 
                              amount: Decimal = None) -> Optional[str]:
        """
        Approve a spender (like a DEX) to spend tokens.
        
        Args:
            chain: The blockchain where the token exists
            token_address: The contract address of the token
            spender_address: The address to approve for spending (e.g., DEX router)
            amount: The amount to approve, or None for unlimited approval
            
        Returns:
            Optional[str]: Transaction hash if successful, None otherwise
        """
        if chain not in self.web3_connections:
            logger.error(f"Chain {chain} not configured")
            return None
        
        w3 = self.web3_connections[chain]
        wallet_address = self.wallets[chain]["address"]
        private_key = self.wallets[chain]["private_key"]
        
        # Create contract instance
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Get token decimals
        decimals = token_contract.functions.decimals().call()
        
        # Set approval amount (max uint256 if None)
        if amount is None:
            approval_amount = 2**256 - 1
        else:
            approval_amount = int(amount * (10 ** decimals))
        
        # Build transaction
        try:
            gas_price_multiplier = self.config["trading"]["gas_price_multiplier"]
            gas_price = int(w3.eth.gas_price * gas_price_multiplier)
            
            # Estimate gas
            gas_estimate = token_contract.functions.approve(
                spender_address, 
                approval_amount
            ).estimate_gas({'from': wallet_address})
            
            # Build transaction
            tx = token_contract.functions.approve(
                spender_address,
                approval_amount
            ).build_transaction({
                'from': wallet_address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(wallet_address),
            })
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Successfully approved {spender_address} to spend tokens")
                return tx_hash.hex()
            else:
                logger.error(f"Token approval failed: {tx_receipt}")
                return None
                
        except Exception as e:
            logger.error(f"Error approving token: {str(e)}")
            return None
    
    def send_token(self, chain: str, token_address: str, to_address: str, 
                  amount: Decimal) -> Optional[str]:
        """
        Send tokens to another address.
        
        Args:
            chain: The blockchain where the token exists
            token_address: The contract address of the token
            to_address: The recipient address
            amount: The amount to send
            
        Returns:
            Optional[str]: Transaction hash if successful, None otherwise
        """
        if chain not in self.web3_connections:
            logger.error(f"Chain {chain} not configured")
            return None
        
        w3 = self.web3_connections[chain]
        wallet_address = self.wallets[chain]["address"]
        private_key = self.wallets[chain]["private_key"]
        
        # Create contract instance
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Get token decimals
        decimals = token_contract.functions.decimals().call()
        
        # Convert amount to token units
        token_amount = int(amount * (10 ** decimals))
        
        # Build transaction
        try:
            gas_price_multiplier = self.config["trading"]["gas_price_multiplier"]
            gas_price = int(w3.eth.gas_price * gas_price_multiplier)
            
            # Estimate gas
            gas_estimate = token_contract.functions.transfer(
                to_address, 
                token_amount
            ).estimate_gas({'from': wallet_address})
            
            # Build transaction
            tx = token_contract.functions.transfer(
                to_address,
                token_amount
            ).build_transaction({
                'from': wallet_address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(wallet_address),
            })
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Successfully sent {amount} tokens to {to_address}")
                return tx_hash.hex()
            else:
                logger.error(f"Token transfer failed: {tx_receipt}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending token: {str(e)}")
            return None
    
    def send_native_token(self, chain: str, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Send native tokens (ETH, BNB, etc.) to another address.
        
        Args:
            chain: The blockchain to use
            to_address: The recipient address
            amount: The amount to send in ether units
            
        Returns:
            Optional[str]: Transaction hash if successful, None otherwise
        """
        if chain not in self.web3_connections:
            logger.error(f"Chain {chain} not configured")
            return None
        
        w3 = self.web3_connections[chain]
        wallet_address = self.wallets[chain]["address"]
        private_key = self.wallets[chain]["private_key"]
        
        # Convert amount to wei
        wei_amount = w3.to_wei(amount, 'ether')
        
        # Build transaction
        try:
            gas_price_multiplier = self.config["trading"]["gas_price_multiplier"]
            gas_price = int(w3.eth.gas_price * gas_price_multiplier)
            
            # Build transaction
            tx = {
                'from': wallet_address,
                'to': to_address,
                'value': wei_amount,
                'gas': 21000,  # Standard gas limit for ETH transfers
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(wallet_address),
            }
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                logger.info(f"Successfully sent {amount} native tokens to {to_address}")
                return tx_hash.hex()
            else:
                logger.error(f"Native token transfer failed: {tx_receipt}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending native token: {str(e)}")
            return None
    
    def get_portfolio_value(self) -> Dict[str, Any]:
        """
        Calculate the total portfolio value across all chains and tokens.
        
        Returns:
            Dict: Portfolio information including total value and breakdown
        """
        portfolio = {
            "total_value_usd": Decimal('0'),
            "chains": {}
        }
        
        # Iterate through each chain
        for chain in self.wallets:
            chain_portfolio = {
                "native_balance": self.get_native_balance(chain),
                "tokens": {}
            }
            
            # Add native token value (would need price feed integration)
            # For now, we'll just record the balance
            
            # Add token balances for tokens of interest
            for token in self.config["tokens_of_interest"]:
                if token["chain"] == chain:
                    balance, _ = self.get_token_balance(chain, token["address"])
                    chain_portfolio["tokens"][token["symbol"]] = {
                        "balance": balance,
                        "address": token["address"]
                    }
            
            portfolio["chains"][chain] = chain_portfolio
        
        return portfolio


if __name__ == "__main__":
    # Example usage
    wallet = BlockchainWallet("../config/config.json")
    
    # Get native balances
    eth_balance = wallet.get_native_balance("ethereum")
    bsc_balance = wallet.get_native_balance("binance_smart_chain")
    
    print(f"ETH Balance: {eth_balance}")
    print(f"BNB Balance: {bsc_balance}")
    
    # Get portfolio
    portfolio = wallet.get_portfolio_value()
    print(json.dumps(portfolio, indent=2, default=str))
