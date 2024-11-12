# Base Imports
import os
import math
import asyncio
import time
from typing import Tuple, Optional

# External Imports
from config import token_configs
from funcs.base_odos import *
from funcs.sol_jupiter import *
from funcs import save_trade_data
from logging_utility import logger

ARB_PERCENT = 1 # Adjust to how aggresive the arbs needs to be
MINIMUM_TOKEN = 10000 # Decides what the minimum token value to swap
MAX_TOKEN = 50000
INCREMENT = 100

MONITOR_DELAY = 1
MONITOR_IMPACT_MIN = 10000

""" Utility """
def parse_price(data, source, out_decimals=6, init_amount=10000.0):
    """
    Parse price data from different sources and normalize the price impact
    
    Args:
        data: Response data from the quote
        source: Source of the quote ("Jupiter" or "Odos")
        out_decimals: Decimals for the output token
        init_amount: Base amount used for the quote (default 1000.0)
    
    Returns:
        tuple: (price_per_token, price_impact_percentage)
    """
    try:
        if source == "Jupiter":
            total_out_amount = float(data['outAmount']) / (10 ** out_decimals)
            price_per_token = total_out_amount / init_amount
            # Jupiter impact is not in percentage need to *100
            impact = float(data['priceImpactPct'])*100
            
            return price_per_token, impact
        
        elif source == "Odos":
            total_out_amount = float(data['outValues'][0])
            price_per_token = total_out_amount / init_amount
            # Convert Odos impact to positive percentage, it is in percent
            impact = abs(float(data['priceImpact']))
            return price_per_token, impact
            
        else:
            print("Invalid Source")
            return None, None
    except Exception as e:
        print(f"Error parsing price for {source}: {e}")
        return None, None

def calc_balanced_swap(base_price, sol_price, base_impact, sol_impact, trade_action):
    """
    Calculate swap amount that ensures equal LUNA amounts on both sides while accounting for price impact
    
    Args:
        base_price: Current price of base token
        sol_price: Current price of sol token
        base_impact: Price impact percentage for base token (0.3 means 0.3%)
        sol_impact: Price impact percentage for sol token (0.3 means 0.3%)
        trade_action: Either 'buy_base_sell_sol' or 'buy_sol_sell_base'
        
    Returns:
        tuple: (token_amount, usdc_amount_base, usdc_amount_sol)
    """
    # Convert impact from percentage to normalized decimals
    base_impact = (base_impact / 100) / math.sqrt(MONITOR_IMPACT_MIN)
    sol_impact = (sol_impact / 100) / math.sqrt(MONITOR_IMPACT_MIN)
    
    if trade_action == 'buy_base_sell_sol':
        # For buy_base_sell_sol:
        # USDC_base -> LUNA_base -> LUNA_sol -> USDC_sol
        # 
        # Amount of LUNA received from base (including impact):
        # luna_base = (usdc_base/base_price) * (1 - base_impact*√x)
        #
        # Amount of LUNA sold on sol (including impact):
        # luna_sol = x
        #
        # For balanced trade: luna_base = luna_sol = x
        # Therefore:
        # x = (usdc_base/base_price) * (1 - base_impact*√x)
        #
        # Solve for usdc_base:
        # x = (usdc_base/base_price) * (1 - base_impact*√x)
        # x*base_price = usdc_base * (1 - base_impact*√x)
        # usdc_base = (x*base_price)/(1 - base_impact*√x)
        
        # Try different LUNA amounts until equations balance
        for x in range(MINIMUM_TOKEN, MAX_TOKEN, INCREMENT):  # Try amounts from 100 to 20000 LUNA
            # Calculate required USDC for base side
            usdc_base = (x * base_price) / (1 - base_impact * math.sqrt(x))
            
            # Calculate expected USDC from sol side
            usdc_sol = x * sol_price * (1 - sol_impact * math.sqrt(x))
            
            # Check if profitable
            profit = usdc_sol - usdc_base
            
            # If profitable and amounts are reasonable
            if profit > 0 and usdc_base > 0 and usdc_sol > 0:
                logger.info(f"\n--------------------------------------\n"   
                f"Calculation for Ideal Swap (Before Quote and Transaction):"
                f"LUNA Amount: {x:.4f}\n"
                f"USDC Base (spent): {usdc_base:.4f}\n"
                f"USDC Sol (received): {usdc_sol:.4f}\n"
                f"Expected Profit: {profit:.4f}\n"
                f"Base Impact: {base_impact * math.sqrt(x) * 100:.4f}%\n"
                f"Sol Impact: {sol_impact * math.sqrt(x) * 100:.4f}%"
                f"--------------------------------------")

                return x, usdc_base, usdc_sol
                
    else:  # buy_sol_sell_base
        # Similar logic but reversed
        for x in range(MINIMUM_TOKEN, MAX_TOKEN, INCREMENT): # Starting, Max, Increment -
            usdc_sol = (x * sol_price) / (1 - sol_impact * math.sqrt(x))
            usdc_base = x * base_price * (1 - base_impact * math.sqrt(x))
            
            profit = usdc_base - usdc_sol
            
            if profit > 0 and usdc_base > 0 and usdc_sol > 0:
                logger.info(f"\n--------------------------------------\n"   
                f"Calculation for Ideal Swap (Before Quote and Transaction):"
                f"LUNA Amount: {x:.4f}\n"
                f"USDC Base (spent): {usdc_base:.4f}\n"
                f"USDC Sol (received): {usdc_sol:.4f}\n"
                f"Expected Profit: {profit:.4f}\n"
                f"Base Impact: {base_impact * math.sqrt(x) * 100:.4f}%\n"
                f"Sol Impact: {sol_impact * math.sqrt(x) * 100:.4f}%"
                f"--------------------------------------")

                return x, usdc_base, usdc_sol
    
    return 0, 0, 0

""" Monitoring """
async def price_checker(delay: int = 1, init_amount: float = 1000.0):
    """
    Modified price checker to use balanced swap calculation.
    Skips rounds where either impact is 0.
    """
    base = token_configs["base"]
    sol = token_configs["solana"]
    
    try:
        # Run both quotes concurrently using gather
        quote_base, quote_sol = await asyncio.gather(
            quote_odos(
                base["tokens"]["luna"]["address"],
                base["tokens"]["usdc"]["address"], 
                init_amount,
                base["tokens"]["luna"]["decimals"],
            ),
            quote_jupiter(
                sol["tokens"]["luna"]["address"],
                sol["tokens"]["usdc"]["address"],
                init_amount,  
                sol["tokens"]["luna"]["decimals"]
            )
        )

        # Parse prices from both sources
        base_price, base_impact = parse_price(quote_base, "Odos", init_amount=init_amount)
        sol_price, sol_impact = parse_price(quote_sol, "Jupiter", sol["tokens"]["usdc"]["decimals"], init_amount=init_amount)
                                
        if base_price and sol_price:
            # Check for zero impacts - skip this round if found
            if base_impact == 0 or sol_impact == 0:
                logger.warning(f"\n--------------------------------------\n"
                            f"Warning: Zero impact detected, skipping round\n"
                            f"Base Impact: {base_impact}\n"
                            f"Sol Impact: {sol_impact}\n"
                            f"--------------------------------------")
                
                await asyncio.sleep(delay)
                return False, None, 0, 0

            avg_price = (base_price + sol_price) / 2
            price_diff = abs(base_price - sol_price) / avg_price * 100
            
            logger.info(f"\n--------------------------------------\n"
            f"Base Price: ${base_price:.6f}\n"
            f"Solana Price: ${sol_price:.6f}\n"
            f"Price Difference: {price_diff:.2f}%\n"
            f"Base Impact ({MONITOR_IMPACT_MIN}): {base_impact}\n"
            f"Sol Impact ({MONITOR_IMPACT_MIN}): {sol_impact}\n"
            f"--------------------------------------")

            # Determine trading action and calculate balanced amounts
            if base_price < sol_price:
                trade_action = "buy_base_sell_sol"
            else:
                trade_action = "buy_sol_sell_base"
            
            if price_diff >= ARB_PERCENT:
                logger.info(f"Arbitrage opportunity found! Action: {trade_action}")
                
                # Calculate balanced amounts
                luna_amount, usdc_base, usdc_sol = calc_balanced_swap(
                    base_price, sol_price, base_impact, sol_impact, trade_action
                )
                
                if luna_amount > 0:
                    # Return the balanced amounts
                    return True, trade_action, luna_amount, usdc_base if trade_action == "buy_base_sell_sol" else usdc_sol
        
        await asyncio.sleep(delay)
        
    except Exception as e:
        logger.error(f"Error in price checker: {e}")
        await asyncio.sleep(delay)
        
    return False, None, 0, 0

def analyze_arb_quotes(quote_base, quote_sol, trade_action):
    """
    Analyze arbitrage quotes and calculate key metrics
    
    Args:
        quote_base: Quote response from Odos
        quote_sol: Quote response from Jupiter
        trade_action: Either 'buy_base_sell_sol' or 'buy_sol_sell_base'
        
    Returns:
        dict: Dictionary containing all key metrics
    """
    try:
        # Initialize variables based on trade direction
        if trade_action == 'buy_base_sell_sol':
            # USDC -> LUNA (Base) and LUNA -> USDC (Sol)
            luna_base = float(quote_base['outAmounts'][0]) / (10 ** 18)  # LUNA received from Base
            usdc_base = float(quote_base['inValues'][0])   # USDC spent on Base
            
            luna_sol = float(quote_sol['inAmount']) / (10 ** 8)  # LUNA spent on Sol
            usdc_sol = float(quote_sol['outAmount']) / (10 ** 6) # USDC received from Sol
            
        else:  # buy_sol_sell_base
            # LUNA -> USDC (Base) and USDC -> LUNA (Sol)
            luna_base = float(quote_base['inAmounts'][0]) / (10 ** 18)   # LUNA spent on Base
            usdc_base = float(quote_base['outValues'][0])  # USDC received from Base
            
            luna_sol = float(quote_sol['outAmount']) / (10 ** 8)  # LUNA received from Sol
            usdc_sol = float(quote_sol['inAmount']) / (10 ** 6)   # USDC spent on Sol
        
        # Calculate profit (in USDC)
        if trade_action == 'buy_base_sell_sol':
            profit = usdc_sol - usdc_base
        else:
            profit = usdc_base - usdc_sol
            
        # Create results dictionary
        results = {
            "action": trade_action,
            "luna_sol": luna_sol,
            "luna_base": luna_base,
            "usdc_sol": usdc_sol,
            "usdc_base": usdc_base,
            "profit_usdc": profit,
        }
        
        # Print detailed analysis
        logger.info(f"\n=== Arbitrage Analysis ===\n"
        f"Action: {trade_action}\n"
        f"LUNA Sol: {luna_sol:.6f}\n"
        f"LUNA Base: {luna_base:.6f}\n"
        f"USDC Sol: ${usdc_sol:.2f}\n"
        f"USDC Base: ${usdc_base:.2f}\n"
        f"Profit: ${profit:.2f}\n"
        f"========================")
                    
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing arbitrage quotes: {e}")
        return None

""" Transactions """
async def execute_arbitrage(
    trade_action: str,
    amount_in: float,
    usd_amount: float,
    base_priv_key: str,
    sol_priv_key: str
) -> Tuple[bool, Optional[str]]:
    """
    Execute the arbitrage trade across both chains
    Returns (success, error_message)
    """
    try:
        # Get addresses from config
        base = token_configs["base"]
        sol = token_configs["solana"]

        # Init tokens based on trade direction
        if trade_action == 'buy_base_sell_sol':
            base_in = base["tokens"]["usdc"]["address"]
            base_out = base["tokens"]["luna"]["address"]
            base_in_dec = base["tokens"]["usdc"]["decimals"]
            base_amount = usd_amount

            sol_in = sol["tokens"]["luna"]["address"]
            sol_out = sol["tokens"]["usdc"]["address"]
            sol_in_dec = sol["tokens"]["luna"]["decimals"]
            sol_amount = amount_in

        else:  # buy_sol_sell_base
            base_in = base["tokens"]["luna"]["address"]
            base_out = base["tokens"]["usdc"]["address"]
            base_in_dec = base["tokens"]["luna"]["decimals"]
            base_amount = amount_in

            sol_in = sol["tokens"]["usdc"]["address"]
            sol_out = sol["tokens"]["luna"]["address"]
            sol_in_dec = sol["tokens"]["usdc"]["decimals"]
            sol_amount = usd_amount

        # Initialize wallet addresses
        base_user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428'
        sol_user_addrs = '9H9kY3pj1t2RdYH9cGDPnXgqh2F7BJvBehboktgVsj1c'

        # Get quotes
        quote_base, quote_sol = await asyncio.gather(
            quote_odos(base_in, base_out, base_amount, base_in_dec, user_addrs=base_user_addrs),
            quote_jupiter(sol_in, sol_out, sol_amount, sol_in_dec)
        )

        # Analyze the quotes
        arb_analysis = analyze_arb_quotes(quote_base, quote_sol, trade_action)
        if not arb_analysis or arb_analysis['profit_usdc'] <= 0:
            return False, "Arbitrage no longer profitable after final quote"

        # Save trade data - Debug
        #save_trade_data(quote_base, 'base.json')
        #save_trade_data(quote_sol, 'sol.json')

        # Assemble transactions
        odos_assembled, jup_assembled = await asyncio.gather(
            assemble_odos(base_user_addrs, quote_base),
            swap_jupiter(sol_user_addrs, quote_sol)
        )

        # Check approvals
        ODOS_ROUTER_V2 = base["odos_routerV2"]
        needs_approval = check_token_approval(base_in, base_user_addrs, ODOS_ROUTER_V2)

        if needs_approval:
            approval_success = send_infinite_approval(base_in, ODOS_ROUTER_V2)
            if not approval_success:
                return False, "Token approval failed"

        # Execute transactions
        base_tx_hash, solana_tx_hash = await asyncio.gather(
            execute_odos(odos_assembled, base_priv_key),
            execute_jupiter(jup_assembled, sol_priv_key)
        )

        logger.info(f"View on Basescan: https://basescan.org/tx/0x{base_tx_hash}")
        logger.info(f"View on Solscan: https://solscan.io/tx/{solana_tx_hash}")

        return True, None

    except Exception as e:
        return False, f"Error executing arbitrage: {str(e)}"

async def main():
    """
    Main function that runs the continuous arbitrage monitoring loop
    """
    # Get private keys from environment
    base_priv_key = os.getenv('BASE_PRIVATE_KEY')
    sol_priv_key = os.getenv('SOL_PRIVATE_KEY')
    
    if not base_priv_key or not sol_priv_key:
        logger.error("Error: Private keys not found in environment variables")
        return

    logger.info("Starting continuous arbitrage monitor...")
    
    while True:
        try:
            # Check for arbitrage opportunity
            arbitrage_check, trade_action, amount_in, usd_amount = await price_checker(delay=1)

            if arbitrage_check:
                logger.info(f"\n!!! ARBITRAGE OPPORTUNITY DETECTED !!!\n"
                f"--------------------------------------\n"
                f"Trade action: {trade_action}\n"
                f"Amount in: {amount_in}\n"
                f"USD amount: {usd_amount}\n"
                f"--------------------------------------")
                
                # Execute the arbitrage
                success, error = await execute_arbitrage(
                    trade_action,
                    amount_in,
                    usd_amount,
                    base_priv_key,
                    sol_priv_key
                )

                if success:
                    logger.info(f"""
                    !!! ARBITRAGE OPPORTUNITY DETECTED !!!
                    --------------------------------------
                    Trade action: {trade_action}
                    Amount in: {amount_in}
                    USD amount: {usd_amount}
                    --------------------------------------""")
                else:
                    logger.error(f"Arbitrage execution failed: {error}")

                # Add a small delay after execution before resuming monitoring
                logger.info(f"Waiting {MONITOR_DELAY} seconds before resuming monitoring...")
                await asyncio.sleep(MONITOR_DELAY)
            else:
                # No arbitrage opportunity found, continue monitoring
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            # Add longer delay on error to prevent rapid retries
            logger.error("Error occurred, waiting 5 seconds before retrying...")
            await asyncio.sleep(5)
            continue

        # Optional: Add periodic status update
        if time.time() % 60 < 1:  # Approximately every minute
            logger.info(f"=== BOT STATUS UPDATE ===\n"
            f"Status: Running\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Activity: Monitoring for arbitrage opportunities\n"
            f"=======================")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"\nBot stopped due to error: {str(e)}")