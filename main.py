# Base Imports
import os
import time
import asyncio

# External Imports
from config import token_configs
from funcs.base_odos import *
from funcs.sol_jupiter import *

def parse_price(data, source, out_decimals=6):

    if source == "Jupiter":
        # Extract outAmount and convert to float considering decimals
        return float(data['outAmount']) / (10 ** out_decimals)  
    elif source == "Odos":
        # Extract price from out_values
        return float(data['outValues'][0])
    else:
        print("Invalid Source")
        return None

async def price_checker(delay: int = 1):
    """
    Continuously checks token price every {delay} seconds
    Returns:
        tuple: (arbitrage_found: bool, trade_action: str)
        where trade_action can be:
        - "buy_base_sell_sol": Buy on Base, sell on Solana
        - "buy_sol_sell_base": Buy on Solana, sell on Base
        - None: No arbitrage opportunity
    """
    
    # Get addresses from config
    base = token_configs["base"]
    sol = token_configs["solana"]
    
    while True:
        try:
            # Run both quotes concurrently using gather
            quote_base, quote_sol = await asyncio.gather(
                quote_odos(
                    base["tokens"]["luna"]["address"],
                    base["tokens"]["usdc"]["address"], 
                    1.0,
                    base["tokens"]["luna"]["decimals"],
                ),
                quote_jupiter(
                    sol["tokens"]["luna"]["address"],
                    sol["tokens"]["usdc"]["address"],
                    1.0,
                    sol["tokens"]["luna"]["decimals"]
                )
            )

            # Parse prices from both sources
            base_price = parse_price(quote_base, "Odos")
            sol_price = parse_price(quote_sol, "Jupiter", sol["tokens"]["usdc"]["decimals"])
                                    
            # Calculate price difference as percentage
            if base_price and sol_price:  # Check if both prices are valid
                avg_price = (base_price + sol_price) / 2
                price_diff = abs(base_price - sol_price) / avg_price * 100
                
                print('--------------------------------------')
                print(f"Base Price: ${base_price:.6f}")
                print(f"Solana Price: ${sol_price:.6f}")
                print(f"Price Difference: {price_diff:.2f}%")
                print('--------------------------------------')

                # Determine trading action
                if base_price < sol_price:
                    trade_action = "buy_base_sell_sol"
                else:
                    trade_action = "buy_sol_sell_base"
                
                if price_diff >= 0.1:
                    print("Arbitrage opportunity found!")
                    print(f"Action: {trade_action}")
                    return True, trade_action
            
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(delay)
            
    return False, None


async def main():

    # Get addresses from config
    base = token_configs["base"]
    sol = token_configs["solana"]

    # Init tokens
    BASE_LUNA = base["tokens"]["luna"]["address"]
    BASE_USDC = base["tokens"]["usdc"]["address"]
    BASE_LUNA_DEC = base["tokens"]["luna"]["decimals"]
    BASE_USDC_DEC = base["tokens"]["usdc"]["decimals"]

    SOL_LUNA = sol["tokens"]["luna"]["address"]
    SOL_USDC = sol["tokens"]["usdc"]["address"]
    SOL_LUNA_DEC = sol["tokens"]["luna"]["decimals"]
    SOL_USDC_DEC = sol["tokens"]["usdc"]["decimals"]

    # 1. Start price checker
    arbitrage_check, trade_action = await price_checker(delay=1)

    # 2. If arbitrage_check == True, decide_direction
    if arbitrage_check == True:
        if trade_action == 'buy_base_sell_sol':
            base_in = BASE_USDC
            base_out = BASE_LUNA
            base_in_dec = BASE_USDC_DEC

            sol_in = SOL_LUNA
            sol_out = SOL_USDC
            sol_in_dec = SOL_LUNA_DEC

        elif trade_action == 'buy_sol_sell_base':
            base_in = BASE_LUNA
            base_out = BASE_USDC
            base_in_dec = BASE_LUNA_DEC

            sol_in = SOL_USDC
            sol_out = SOL_LUNA
            sol_in_dec = SOL_USDC_DEC
        else:
            print('Invalid Action')

    # 3. Decide best amount to swap -- VERY CRUCIAL DONT KNOW HOW TO DO YET
    amount = 1.0

    # 4. Initialize wallet, ie: wallet address
    base_user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428'
    sol_user_addrs = '9H9kY3pj1t2RdYH9cGDPnXgqh2F7BJvBehboktgVsj1c'

    # 5. Call quotes
    quote_base, quote_sol = await asyncio.gather(
        quote_odos(base_in, base_out, amount, base_in_dec),
        quote_jupiter(sol_in, sol_out, amount, sol_in_dec)
    )

    print(quote_base)
    print(quote_sol)


    # 6. Assemble using assemble_odos
    assembled_transaction = assemble_odos(user_addrs, path_id)

    # Pre - Get token approval
    needs_approval = check_token_approval(in_token, user_addrs, ODOS_ROUTER_V2)

    if needs_approval:
        print("Token approval needed. Sending approval transaction...")
        approval_success = send_infinite_approval(in_token, ODOS_ROUTER_V2)
        if not approval_success:
            print("Approval failed!")
            return
        print("Approval successful!")

    # 7. Execute Transaction 
    tx_hash = execute_transaction(assembled_transaction)

    # 8. Print Results
    print(tx_hash)

asyncio.run(main())