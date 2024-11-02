import os
from decimal import Decimal

# External
import requests
import base58
import asyncio 
from dotenv import load_dotenv
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  
from solders.transaction import VersionedTransaction
from solders.message import Message
from solders.signature import Signature
from base64 import b64decode


load_dotenv()

# Utils
def convert_to_decimal_amount(amount: float, decimals: int) -> str:
    """Convert human readable amount to token decimal precision."""
    scale = Decimal(10) ** decimals
    return str(int(Decimal(str(amount)) * scale))

def convert_from_decimal_amount(amount: str, decimals: int) -> float:
    """Convert token decimal precision to human readable amount."""
    scale = Decimal(10) ** decimals
    return float(Decimal(amount) / scale)

# Core
def quote_jupiter(in_token: str, out_token: str, amount: float, in_decimals: int) -> dict:
    """Get a quote from Jupiter for token swap."""
    decimal_amount = convert_to_decimal_amount(amount, in_decimals)

    url = f"https://quote-api.jup.ag/v6/quote?inputMint={in_token}&outputMint={out_token}&amount={decimal_amount}"

    headers = {
        'Accept': 'application/json'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def swap_jupiter(quote_response: dict, user_public_key: str) -> dict:
    """Create a swap transaction using Jupiter API."""
    swap_payload = {
        "quoteResponse": quote_response,
        "userPublicKey": user_public_key,
        "wrapUnwrapSOL": True,
        "computeUnitPriceMicroLamports": None,
        "asLegacyTransaction": False
    }
    
    url = "https://quote-api.jup.ag/v6/swap"
    
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=swap_payload)
    response.raise_for_status()
    return response.json()

async def execute_swap(swap_data, sol_private_key, sol_rpc):
    # Convert base58 private key to bytes
    private_key_bytes = base58.b58decode(sol_private_key)

    # Create keypair from bytes
    wallet = Keypair.from_bytes(private_key_bytes)

    # Create RPC connection
    connection = AsyncClient(sol_rpc)

    try:
        # Extract the swap transaction from the dictionary
        swap_transaction = swap_data['swapTransaction']

        # Sign Transaction Data
        transaction_bytes = b64decode(swap_transaction)
        #transaction = VersionedTransaction.from_bytes(transaction_bytes)
        #transaction.sign([wallet])

        tx = VersionedTransaction.from_bytes(transaction_bytes)
        signed_tx = VersionedTransaction(tx.message, [wallet])
        signed_tx_bytes = bytes(signed_tx)

        # Get the latest block hash
        latest_block_hash = await connection.get_latest_blockhash()

        #Execute the transaction
        txid = await connection.send_raw_transaction(
            signed_tx_bytes
        )

        # Confirm the transaction
        await connection.confirm_transaction(
            txid,
            latest_block_hash.value.blockhash
        )

        return txid
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e
    finally:
        # Always close the connection
        await connection.close()

async def main():
    # Constants
    LUNA_SOL = '9se6kma7LeGcQWyRBNcYzyxZPE3r9t9qWZ8SnjnN3jJ7'
    DECIMAL_LUNA = 8
    USDC_SOL = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
    DECIMAL_USDC = 6

    PUBLIC_KEY = '9H9kY3pj1t2RdYH9cGDPnXgqh2F7BJvBehboktgVsj1c'
    
    # Get environment variables
    sol_private_key = os.getenv('SOL_PRIVATE_KEY')
    sol_rpc = os.getenv('SOL_RPC')

    if not sol_private_key or not sol_rpc:
        raise ValueError("Missing required environment variables")

    # Execute swap steps
    quote = quote_jupiter(LUNA_SOL, USDC_SOL, 1.0, DECIMAL_LUNA)
    swap_data = swap_jupiter(quote, PUBLIC_KEY)
    
    try:
        txid = await execute_swap(swap_data, sol_private_key, sol_rpc)
        print(f"Swap completed with transaction ID: {txid}")
        print(f"https://solscan.io/tx/{txid}")
    except Exception as e:
        print(f"Failed to execute swap: {str(e)}")

# Proper way to run async code
if __name__ == "__main__":
    asyncio.run(main())

