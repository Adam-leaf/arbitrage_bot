# Base Imports
import os
from decimal import Decimal

# External Imports
import aiohttp
from contracts.abi.erc20_approve_abi import erc20_abi
from funcs import w3 , w3_async

# Utils
def convert_to_decimal_amount(amount: float, decimals: int) -> str:
    """Convert human readable amount to token decimal precision."""
    scale = Decimal(10) ** decimals
    return str(int(Decimal(str(amount)) * scale))

def parse_path_id(odos_quote):
    try:
        return str(odos_quote['pathId'])
    except (KeyError, ValueError) as e:
        raise Exception(f"Error parsing Odos pathId: {str(e)}")

# Quote and Assemble
async def quote_odos(in_token, out_token, amount, in_decimals, chain_id = '8453', user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428', slippage = 0.3):
    """
    Get a quote from Odos API for token swaps.
    
    Args:
        in_token: The address of the input token
        out_token: The address of the output token
        amount: Amount of input token
        in_decimals: Decimals of input token
        chain_id: Chain ID - 8453 for Base
        user_addrs: User address for the quote
        slippage: Maximum slippage tolerance in percentage
    """
    
    base_url = "https://api.odos.xyz"
    decimal_amount = convert_to_decimal_amount(amount, in_decimals)
    
    payload = {
        "chainId": chain_id,
        "inputTokens": [
            {
                "tokenAddress": in_token,
                "amount": decimal_amount
            }
        ],
        "outputTokens": [
            {
                "tokenAddress": out_token,
                "proportion": 1
            }
        ],
        "userAddr": user_addrs,
        "slippageLimitPercent": slippage,
        "sourceBlacklist": [],
        "sourceWhitelist": [],
        "compact": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/sor/quote/v2",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                response.raise_for_status()
                return await response.json()
                
    except aiohttp.ClientError as e:
        raise Exception(f"Error fetching quote from Odos API: {str(e)}")

async def assemble_odos(user_addrs, odos_quote):
    """ Assemble the odos quote asynchronously """

    pathId = parse_path_id(odos_quote)
    base_url = "https://api.odos.xyz"
    
    payload = {
        "userAddr": user_addrs,
        "pathId": pathId,
        "simulate": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/sor/assemble",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise Exception(f"Error fetching quote from Odos API: {str(e)}")

# Check Approval
def check_token_approval(token_address, owner_address, spender_address):
    """Check if token approval is needed"""

    token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)
    current_allowance = token_contract.functions.allowance(owner_address, spender_address).call()
    
    # Check if current allowance is "infinite enough" (very large number)
    LARGE_APPROVAL_THRESHOLD = 2**200  # If allowance is above this, we consider it infinite
    return current_allowance < LARGE_APPROVAL_THRESHOLD

def send_infinite_approval(token_address, spender_address):
    """Send infinite token approval transaction"""
    
    token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)
    private_key = os.getenv("PRIVATE_KEY")
    account = w3.eth.account.from_key(private_key)
    
    # Maximum uint256 value for infinite approval
    MAX_INT = 2**256 - 1
    
    # Get the latest nonce and gas price
    latest_nonce = w3.eth.get_transaction_count(account.address, 'latest')
    gas_price = w3.eth.gas_price
    
    print(f"Using nonce: {latest_nonce}")
    
    try:
        # Build approval transaction
        approve_tx = token_contract.functions.approve(
            spender_address,
            MAX_INT
        ).build_transaction({
            'from': account.address,
            'nonce': latest_nonce,
            'gas': 100000,
            'gasPrice': gas_price,
            'chainId': 8453  # Base chain ID
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        print(f"Waiting for infinite approval transaction {tx_hash.hex()} to be mined...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_receipt['status'] == 1
        
    except Exception as e:
        print(f"Error in approval transaction: {str(e)}")
        return False

# Execute Transaction
async def execute_odos(assembled_transaction, private_key, chain_id=8453):
    """ Execute a transaction and check its status asynchronously """

    transaction = assembled_transaction["transaction"]
    transaction["chainId"] = chain_id
    transaction["value"] = int(transaction["value"])
    
    try:
        # Sign and send transaction
        signed_tx = w3_async.eth.account.sign_transaction(transaction, private_key)
        tx_hash = await w3_async.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        print(f"Base -> Transaction sent: {tx_hash.hex()}")
        tx_receipt = await w3_async.eth.wait_for_transaction_receipt(tx_hash)
        
        # Check transaction status
        if tx_receipt['status'] == 1:
            return tx_hash.hex()
            
            # Debug
            # return {
            #     'success': True,
            #     'hash': tx_hash.hex(),
            #     'receipt': tx_receipt
            # }
            
        else:
            # Try to get revert reason
            try:
                tx = await w3.eth.get_transaction(tx_hash)
                # Simulate the failed transaction to get the revert reason
                await w3.eth.call(
                    {
                        'from': tx['from'],
                        'to': tx['to'],
                        'data': tx['input'],
                        'value': tx['value'],
                        'gas': tx['gas'],
                        'gasPrice': tx['gasPrice'],
                    },
                    tx_receipt['blockNumber']
                )
            except Exception as call_error:
                error_message = str(call_error)
                return {
                    'success': False,
                    'hash': tx_hash.hex(),
                    'error': f"Transaction reverted: {error_message}",
                    'receipt': tx_receipt
                }
            
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to send transaction: {str(e)}"
        }