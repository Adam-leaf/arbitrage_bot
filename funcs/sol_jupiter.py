import base64
import time
from decimal import Decimal

# External
import aiohttp
import base58
import asyncio 
from solders.keypair import Keypair  
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from funcs import sol_client, sol_client_async

# Utils
def convert_to_decimal_amount(amount: float, decimals: int) -> str:
    """Convert human readable amount to token decimal precision."""
    scale = Decimal(10) ** decimals
    return str(int(Decimal(str(amount)) * scale))

def convert_from_decimal_amount(amount: str, decimals: int) -> float:
    """Convert token decimal precision to human readable amount."""
    scale = Decimal(10) ** decimals
    return float(Decimal(amount) / scale)

def wait_for_confirmation(signature, max_retries: int = 60, retry_delay: int = 2) -> bool:
    """
    Wait for transaction confirmation with extended timeout and detailed status checking.
    """
    print(f"Waiting for transaction confirmation: {signature}")
    last_status = None
    
    for attempt in range(max_retries):
        try:
            response = sol_client.get_signature_statuses([signature])
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
                #print(f"Waiting for confirmation... Attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
            
        except Exception as e:
            print(f"Error checking confirmation: {str(e)}")
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                time.sleep(retry_delay)
    
    return False

# Core
async def quote_jupiter(in_token, out_token, amount, in_decimals):
    """Get a quote from Jupiter for token swap."""
    decimal_amount = convert_to_decimal_amount(amount, in_decimals)
    
    url = f"https://quote-api.jup.ag/v6/quote?inputMint={in_token}&outputMint={out_token}&amount={decimal_amount}"
    headers = {'Accept': 'application/json'}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

async def swap_jupiter(user_public_key, quote_response):
    """Create a swap transaction using Jupiter API asynchronously."""
    
    swap_data = {
        "quoteResponse": quote_response,
        "userPublicKey": user_public_key,
        "wrapUnwrapSOL": True,
        "computeUnitPriceMicroLamports": None,
        "asLegacyTransaction": False,
        "useSharedAccounts": True,
        "prioritizationFeeLamports": 500_000
    }
    
    url = "https://quote-api.jup.ag/v6/swap"
    headers = {"Content-Type": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=swap_data) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Error response: {error_text}")
            response.raise_for_status()
            
            return await response.json()

async def execute_jupiter(swap_data, sol_private_key):
    """Execute a swap transaction asynchronously."""
    
    private_key_bytes = base58.b58decode(sol_private_key)
    keypair = Keypair.from_bytes(private_key_bytes)
    
    try:
        # Decode and sign transaction
        swap_tx = base64.b64decode(swap_data['swapTransaction'])
        tx = VersionedTransaction.from_bytes(swap_tx)
        signed_tx = VersionedTransaction(tx.message, [keypair])
        signed_tx_bytes = bytes(signed_tx)
        
        # Send transaction using async API
        tx_opts = TxOpts(skip_preflight=True, max_retries=5)
        tx_response = await sol_client_async.send_raw_transaction(signed_tx_bytes, opts=tx_opts)
        
        if tx_response.value:
            tx_sig = tx_response.value
            print(f"Solana -> Transaction sent: {tx_sig}")
            
            # Async wait for confirmation
            async def check_confirmation():
                retries = 0
                max_retries = 60
                retry_delay = 2
                
                while retries < max_retries:
                    try:
                        response = sol_client.get_signature_statuses([tx_sig])
                        
                        if response and response.value[0]:
                            status = response.value[0]
                            confirmation_str = str(status.confirmation_status)
                            result = confirmation_str.split(".")[-1]

                            # Check if transaction is finalized, regardless of success/error
                            if result == "Finalized":
                                # If there's an error, include it in the return
                                if status.err:
                                    print(f"Transaction finalized with error: {status.err}")
                                return True, status.err
                            print(f"Current status: {result} (Confirmations: {status.confirmations})")
                    except Exception as e:
                        print(f"Confirmation attempt {retries + 1} failed: {str(e)}")
                    
                    retries += 1
                    await asyncio.sleep(retry_delay)
                return False, None
            
            is_finalized, error = await check_confirmation()
            if is_finalized:
                if error:
                    print(f"Transaction finalized with error: {error}")
                else:
                    print("Transaction successfully finalized!")
                return tx_sig
            else:
                raise Exception("Transaction confirmation timeout or failed to finalize")
        else:
            raise Exception("No transaction ID returned")
            
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        raise e