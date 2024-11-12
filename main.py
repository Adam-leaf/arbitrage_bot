# Base Imports
import os
import math
import asyncio

# External Imports
from config import token_configs
from funcs.base_odos import *
from funcs.sol_jupiter import *
from funcs import save_trade_data

""" Core Arb Execution """
def parse_price(data, source, out_decimals=6, init_amount=1000.0):
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

def calc_ideal_swap(base_price, sol_price, base_impact, sol_impact, trade_action, target=50):
    """
    Calculate ideal swap amount to close price gap by target percentage
    
    Args:
        base_price: Current price of base token
        sol_price: Current price of sol token
        base_impact: Price impact percentage for base token (0.3 means 0.3%)
        sol_impact: Price impact percentage for sol token (0.3 means 0.3%)
        trade_action: Either 'buy_base_sell_sol' or 'buy_sol_sell_base'
        target: Target percentage of gap to close (default 100%)
        
    Returns:
        tuple: (token_amount, usdc_needed)
    """
    # Simulate
    # trade_action = 'buy_base_sell_sol'
    # base_price = 0.09100
    # sol_price = 0.09151
    # base_impact = 0.06  
    # sol_impact = 0.5  

    # Convert impact from percentage to decimal
    base_impact = base_impact / 100
    sol_impact = sol_impact / 100
    print(f"Ori: Base - {base_impact}, Sol - {sol_impact}")
    
    # These impacts are for 1000 token swap, so we need to normalize them
    # If impact is p% for 1000 tokens, then for x tokens it's p * sqrt(x/1000)
    # So we need to divide our impact coefficients by sqrt(1000)
    base_impact = base_impact / math.sqrt(1000)
    sol_impact = sol_impact / math.sqrt(1000)

    print(f"Mod: Base - {base_impact}, Sol - {sol_impact}")

    # Calculate initial gap
    initial_gap = abs(sol_price - base_price)
    target_gap = initial_gap * (1 - target/100)
    
    if trade_action == 'buy_base_sell_sol':
        # New price after swap for amount x:
        # base_new = base_price * (1 + base_impact*√x)
        # sol_new = sol_price * (1 - sol_impact*√x)
        # We want: base_new - sol_new = target_gap
        
        # Solving the equation:
        # base_price*(1 + base_impact*√x) - sol_price*(1 - sol_impact*√x) = target_gap
        # base_price + base_price*base_impact*√x - sol_price + sol_price*sol_impact*√x = target_gap
        # (base_price*base_impact + sol_price*sol_impact)*√x = target_gap - (base_price - sol_price)
        # √x = (target_gap - (base_price - sol_price)) / (base_price*base_impact + sol_price*sol_impact)
        
        root_amount = (target_gap - (base_price - sol_price)) / (base_price * base_impact + sol_price * sol_impact)
        if root_amount < 0:
            return 0, 0
        amount = root_amount * root_amount
        
        # Calculate USDC needed for trade
        usdc_amount = amount * base_price * (1 + base_impact*math.sqrt(amount))
        
    else:  # buy_sol_sell_base
        # Similar equation but for opposite direction:
        # sol_price*(1 + sol_impact*√x) - base_price*(1 - base_impact*√x) = target_gap
        
        root_amount = (target_gap - (sol_price - base_price)) / (sol_price * sol_impact + base_price * base_impact)
        if root_amount < 0:
            return 0, 0
        amount = root_amount * root_amount
        
        usdc_amount = amount * sol_price * (1 + sol_impact*math.sqrt(amount))
    
    print(f"""
        Direct Calculation Results:
        LUNA Amount: {amount:.4f}
        USDC Amount: {usdc_amount:.4f}
        BASE PRICE: {base_price}
        SOL_PRICE: {sol_price}
        Initial Gap: {initial_gap}
        Target Gap: {target_gap:.6f}
    """)

    return amount, usdc_amount

async def price_checker(delay: int = 1, init_amount: float = 1000.0):
    """
    Continuously checks token price every {delay} seconds
    Args:
        delay: Time between checks in seconds
        init_amount: Base amount to use for price quotes (e.g. 1000 LUNA)
    Returns:
        tuple: (arbitrage_found: bool, trade_action: str, amount: float, usd_amount: float)
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

            # Parse prices from both sources, passing the base_amount
            base_price, base_impact = parse_price(quote_base, "Odos", init_amount=init_amount)
            sol_price, sol_impact = parse_price(quote_sol, "Jupiter", sol["tokens"]["usdc"]["decimals"], init_amount=init_amount)
                                    
            # Calculate price difference as percentage
            if base_price and sol_price:  # Check if both prices are valid
                avg_price = (base_price + sol_price) / 2
                price_diff = abs(base_price - sol_price) / avg_price * 100
                
                print('--------------------------------------')
                print(f"Base Price: ${base_price:.6f}")
                print(f"Solana Price: ${sol_price:.6f}")
                print(f"Price Difference: {price_diff:.2f}%")
                print(f"Base Impact: {base_impact}")
                print(f"Sol Impact: {sol_impact}")
                print('--------------------------------------')

                # Determine trading action
                if base_price < sol_price:
                    trade_action = "buy_base_sell_sol"
                else:
                    trade_action = "buy_sol_sell_base"
                
                if price_diff >= 1:
                    print("Arbitrage opportunity found!")
                    print(f"Action: {trade_action}")
                    
                    # Calc Ideal Swap amount
                    amount, usd_amount = calc_ideal_swap(base_price, sol_price, base_impact, sol_impact, trade_action)
                    return True, trade_action, amount, usd_amount
            
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(delay)
            
    return False, None, 0, 0

""" Calculating Profits """
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
            "profit_bps": (profit / min(usdc_sol, usdc_base)) * 10000  # Profit in basis points
        }
        
        # Print detailed analysis
        print("\n=== Arbitrage Analysis ===")
        print(f"Action: {trade_action}")
        print(f"LUNA Sol: {luna_sol:.6f}")
        print(f"LUNA Base: {luna_base:.6f}")
        print(f"USDC Sol: ${usdc_sol:.2f}")
        print(f"USDC Base: ${usdc_base:.2f}")
        print(f"Profit: ${profit:.2f} ({results['profit_bps']:.1f} bps)")
        print("========================\n")
        
        return results
        
    except Exception as e:
        print(f"Error analyzing arbitrage quotes: {e}")
        return None


async def main():

    # Get addresses from config
    base = token_configs["base"]
    sol = token_configs["solana"]
    base_priv_key = os.getenv('BASE_PRIVATE_KEY')
    sol_priv_key = os.getenv('SOL_PRIVATE_KEY')

    # Init tokens
    BASE_LUNA = base["tokens"]["luna"]["address"]
    BASE_USDC = base["tokens"]["usdc"]["address"]
    BASE_LUNA_DEC = base["tokens"]["luna"]["decimals"]
    BASE_USDC_DEC = base["tokens"]["usdc"]["decimals"]

    SOL_LUNA = sol["tokens"]["luna"]["address"]
    SOL_USDC = sol["tokens"]["usdc"]["address"]
    SOL_LUNA_DEC = sol["tokens"]["luna"]["decimals"]
    SOL_USDC_DEC = sol["tokens"]["usdc"]["decimals"]

    # Init Odos Contract
    ODOS_ROUTER_V2 = base["odos_routerV2"]
    
    # 1. Start price checker - Will auto calc, amount to swap
    arbitrage_check, trade_action, amount_in, usd_amount = await price_checker(delay=1)

    # 2. If arbitrage_check == True, decide_direction
    if arbitrage_check == True:
        if trade_action == 'buy_base_sell_sol':
            base_in = BASE_USDC
            base_out = BASE_LUNA
            base_in_dec = BASE_USDC_DEC
            base_amount = usd_amount

            sol_in = SOL_LUNA
            sol_out = SOL_USDC
            sol_in_dec = SOL_LUNA_DEC
            sol_amount = amount_in

        elif trade_action == 'buy_sol_sell_base':
            base_in = BASE_LUNA
            base_out = BASE_USDC
            base_in_dec = BASE_LUNA_DEC
            base_amount = amount_in

            sol_in = SOL_USDC
            sol_out = SOL_LUNA
            sol_in_dec = SOL_USDC_DEC
            sol_amount = usd_amount

        else:
            print('Invalid Action')

    # 4. Initialize wallet, ie: wallet address
    base_user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428'
    sol_user_addrs = '9H9kY3pj1t2RdYH9cGDPnXgqh2F7BJvBehboktgVsj1c'

    # 5. Quote
    quote_base, quote_sol = await asyncio.gather(
        quote_odos(base_in, base_out, base_amount, base_in_dec, user_addrs = base_user_addrs),
        quote_jupiter(sol_in, sol_out, sol_amount, sol_in_dec)
    )

    # Analyze the quotes
    arb_analysis = analyze_arb_quotes(quote_base, quote_sol, trade_action)
    print(arb_analysis)
    save_trade_data(quote_base, 'base.json')
    save_trade_data(quote_sol, 'sol.json')

    # 6. Assemble 
    odos_assembled, jup_assembled = await asyncio.gather(
        assemble_odos(base_user_addrs, quote_base),
        swap_jupiter(sol_user_addrs, quote_sol)
    )

    print("Swap transaction assembled")

    # 7. Approval Checks for Base
    needs_approval = check_token_approval(base_in, base_user_addrs, ODOS_ROUTER_V2)

    if needs_approval:
        print("Token approval needed. Sending approval transaction...")
        approval_success = send_infinite_approval(base_in, ODOS_ROUTER_V2)
        if not approval_success:
            print("Approval failed!")
            return
        print("Approval successful!")

    # 8. Execute Transaction 
    base_tx_hash, solana_tx_hash = await asyncio.gather(
        execute_odos(odos_assembled, base_priv_key),
        execute_jupiter(jup_assembled, sol_priv_key)
    )

    # 9. Print Results
    print(f"View on Basescan: https://basescan.org/tx/0x{base_tx_hash}")
    print(f"View on Solscan: https://solscan.io/tx/{solana_tx_hash}")

asyncio.run(main())