import os
import json
import time
from decimal import Decimal
import base64

# External
import requests
import base58
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts

load_dotenv()

def convert_to_decimal_amount(amount: float, decimals: int) -> str:
    """Convert human readable amount to token decimal precision."""
    scale = Decimal(10) ** decimals
    return str(int(Decimal(str(amount)) * scale))

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
    # Print the quote response for debugging
    print(f"Quote Response received: {json.dumps(quote_response, indent=2)}")
    
    swap_data = {
        "quoteResponse": quote_response,
        "userPublicKey": user_public_key,
        "wrapUnwrapSOL": True,
        "computeUnitPriceMicroLamports": None,
        "asLegacyTransaction": False,
        "useSharedAccounts": True,
        "prioritizationFeeLamports": 4_000_000
    }
    
    url = "https://quote-api.jup.ag/v6/swap"
    print(f"Swap request data: {json.dumps(swap_data, indent=2)}")
    
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=swap_data
    )
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    response.raise_for_status()
    
    return response.json()

def wait_for_confirmation(client: Client, signature: str, max_retries: int = 60, retry_delay: int = 2) -> bool:
    """
    Wait for transaction confirmation with extended timeout and detailed status checking.
    """
    print(f"Waiting for transaction confirmation: {signature}")
    last_status = None
    
    for attempt in range(max_retries):
        try:
            response = client.get_signature_statuses([signature])
            if response.value[0] is not None:
                confirmation_status = str(response.value[0].confirmation_status)
                
                # Only print status if it has changed
                if confirmation_status != last_status:
                    print(f"Current status: {confirmation_status}")
                    last_status = confirmation_status
                
                # Check if status is finalized
                if "finalized" in confirmation_status.lower():
                    print(f"Transaction finalized after {attempt * retry_delay} seconds")
                    return True
            
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                print(f"Waiting for confirmation... Attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
            
        except Exception as e:
            print(f"Error checking confirmation: {str(e)}")
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                time.sleep(retry_delay)
    
    return False

def execute_swap(swap_data, sol_private_key, sol_rpc):
    """Execute a swap transaction."""
    # Set up client and wallet
    client = Client(sol_rpc)
    private_key_bytes = base58.b58decode(sol_private_key)
    keypair = Keypair.from_bytes(private_key_bytes)
    
    try:
        # Decode and sign transaction
        swap_tx = base64.b64decode(swap_data['swapTransaction'])
        tx = VersionedTransaction.from_bytes(swap_tx)
        signed_tx = VersionedTransaction(tx.message, [keypair])
        signed_tx_bytes = bytes(signed_tx)
        
        # Send transaction
        tx_opts = TxOpts(skip_preflight=True, max_retries=5)
        tx_response = client.send_raw_transaction(signed_tx_bytes, opts=tx_opts)
        
        if tx_response.value:
            print(f"Transaction sent: {tx_response.value}")
            
            # Wait for confirmation with extended timeout
            if wait_for_confirmation(client, tx_response.value, max_retries=60, retry_delay=2):
                print("Transaction successfully finalized!")
                return tx_response.value
            else:
                raise Exception("Transaction confirmation timeout or failed to finalize")
        else:
            raise Exception("No transaction ID returned")
            
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        raise e

def main():
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

    try:
        # Get quote
        quote = quote_jupiter(LUNA_SOL, USDC_SOL, 1.0, DECIMAL_LUNA)
        print("Quote received successfully")
        
        # Create swap transaction
        swap_data = swap_jupiter(quote, PUBLIC_KEY)
        print("Swap transaction created")
        
        # Execute swap
        txid = execute_swap(swap_data, sol_private_key, sol_rpc)
        print(f"Swap completed successfully!")
        print(f"Transaction ID: {txid}")
        print(f"View on Solscan: https://solscan.io/tx/{txid}")
        
    except Exception as e:
        print(f"Error during swap process: {str(e)}")
        raise e

if __name__ == "__main__":
    main()