from fetchdata import fetch_price_data
from parameters import Parameters
import pickle, time, math, tqdm, subprocess, os
import numpy as np

class SignalGenerator:
    def __init__(self, symbols, parameters):
        self.symbols = symbols
        self.parameters = parameters
        self.unallocated_funds = 1000000
        self.all_time_high = 0
        self.all_time_low = float('inf')

        try:
            os.mkdir("logs")
        except:
            pass

    def getdata(self):
        print("Fetching current price data...")
        data = fetch_price_data(self.symbols, period=self.parameters.period, interval="1m")
        print()
        return data
    
    def score_universe(self, data):
        volatilities, momentums = {}, {}

        for symbol, prices in data.items():
            if len(prices)>0:
                normalized_volatility = prices.std() / prices.mean()
                mom_window = self.parameters.mom_window if len(prices) >= self.parameters.mom_window else len(prices)
                normalized_momentum = (prices[-1] - prices[-mom_window]) / prices[-mom_window]
                if math.isnan(normalized_volatility) or math.isnan(normalized_momentum):
                    continue
                volatilities[symbol] = normalized_volatility
                momentums[symbol] = normalized_momentum

        # Top N symbols by volatility
        top_vol = sorted(volatilities.items(), key=lambda x: x[1], reverse=True)[:self.parameters.top_n_volatility]

        # Rank by momentum
        ranked_symbols = sorted(top_vol, key=lambda x: momentums[x[0]], reverse=True)

        ranked_stocks = []
        for s, _  in ranked_symbols:
            ranked_stocks.append(s)

        return ranked_stocks
    
    def allocate_funds(self):
        data           = self.getdata()
        ranked_stocks = self.score_universe(data)

        print(ranked_stocks)

        # Allocate funds to the top K symbols
        self.allocation = {}
        self.buy_price  = {}
        investable_stocks = ranked_stocks[:self.parameters.num_stocks_to_long]
        for symbol in investable_stocks:
            self.allocation[symbol] = self.unallocated_funds / len(investable_stocks)
            self.buy_price[symbol] = data[symbol][-1]  # Last price in the data

        state = {
            'allocation'        : self.allocation,
            'buy_price'         : self.buy_price,
            "all_time_high"     : 0.0,
            "all_time_low"      : float('inf'),
                }

        # Save the last state
        with open('last_state.pkl', 'wb') as f:
            pickle.dump(state, f)

        for symbol, allocation in self.allocation.items():
            print(f"Buy {symbol} \t Allocation: {allocation:.2f} \t Buy Price: {self.buy_price[symbol]:.2f}")
        print()
        print("________FUNDS ALLOCATED________")

    def load_state(self, state):
        self.allocation        = state['allocation']
        self.buy_price         = state['buy_price']
        self.all_time_high     = state["all_time_high"]
        self.all_time_low      = state["all_time_low"]

    def sell_and_buy(self, current_price_data):
        stocks_to_sell = []
        stocks_to_buy  = []
        unallocated_funds = 0
        current_valuations = {}

        for symbol, allocation in self.allocation.items():
            current_price = current_price_data[symbol][-1]
            buy_price     = self.buy_price[symbol]            
            percentage_change = ((current_price - buy_price) / buy_price)

            if (percentage_change > self.parameters.percentage_change_threshold) or (percentage_change < -5*self.parameters.percentage_change_threshold):
                stocks_to_sell.append(symbol)
                unallocated_funds += allocation + (allocation * percentage_change)

            current_valuations[symbol] = allocation + (allocation * percentage_change)

        if len(stocks_to_sell) > 0:
            ranked_stocks = self.score_universe(current_price_data)

            while len(stocks_to_buy) < len(stocks_to_sell):
                stock = ranked_stocks.pop(0)
                if stock not in self.allocation.keys():
                    stocks_to_buy.append(stock)

            # Remove from allocation
            for symbol in stocks_to_sell:
                del self.allocation[symbol]
                del self.buy_price[symbol]

            # Reallocate funds to the new stocks
            for symbol in stocks_to_buy:
                self.allocation[symbol] = unallocated_funds / len(stocks_to_buy)
                self.buy_price[symbol]  = current_price_data[symbol][-1]
                current_valuations[symbol] = unallocated_funds / len(stocks_to_buy)

            with open('last_state.pkl', 'wb') as f:
                state = {
                    'allocation'        : self.allocation,
                    'buy_price'         : self.buy_price,
                    "all_time_high"     : self.all_time_high,
                    "all_time_low"      : self.all_time_low,
                }
                pickle.dump(state, f)

        return stocks_to_sell, stocks_to_buy, current_valuations
    
    def execute_trade(self, stocks_to_sell, stocks_to_buy, current_valuations):
        trade_data = ""
        if len(stocks_to_sell) > 0:
            for symbol in stocks_to_sell:
                trade_data += f"Selling stock: {symbol} \t Current Value: {current_valuations[symbol]:.2f}\n"
                
        if len(stocks_to_buy) > 0:
            for symbol in stocks_to_buy:
                trade_data += f"Buying stock: {symbol} \t Allocation: {self.allocation[symbol]:.2f}\n"

        print()
        print(trade_data)
        print()

        return trade_data
                
    def start(self):
        # Try loading the last saved state
        try:
            with open('last_state.pkl', 'rb') as f:
                last_state = pickle.load(f)
                self.load_state(last_state)

        except FileNotFoundError:
            last_state = None

        if not last_state:
            self.allocate_funds()

        self.run_trading()

    def show_current_info(self, current_price_data):
        total_value = 0
        for symbol, allocation in self.allocation.items():
            buy_price = self.buy_price[symbol]
            current_price = current_price_data[symbol][-1]
            percentage_change = ((current_price - buy_price) / buy_price)
            current_value = allocation + (allocation * percentage_change)
            total_value += current_value

        if total_value > self.all_time_high:
            self.all_time_high = total_value
        if total_value < self.all_time_low:
            self.all_time_low = total_value

        display_data = "                           CURRENT PORTFOLIO                           "
        display_data += "\n\n"

        for symbol, allocation in self.allocation.items():
            buy_price = self.buy_price[symbol]
            current_price = current_price_data[symbol][-1]
            percentage_change = ((current_price - buy_price) / buy_price) * 100
            display_data += f"Stock: {symbol} \t Percentage change: {percentage_change:.4f}% \t Current Value: ${allocation + (allocation * percentage_change / 100):.2f}"
            display_data += "\n"
        display_data += "\n"
        display_data += "Current Portfolio Value : ${:.2f} \n".format(total_value)
        #display_data += "All Time High           : ${:.2f} \n".format(self.all_time_high)
        #display_data += "All Time Low            : ${:.2f} \n".format(self.all_time_low)
        display_data += "                                                                       "
        display_data += "\n\n"

        print(display_data)

        return display_data
    
    def publish_data(self, data, filename, itr):
        with open(filename, "w") as f:
            f.write(data)

        commit_message = f"{itr}"
        branch = "main"

        subprocess.run(["git", "add", filename])
        subprocess.run(["git", "commit", "-m", commit_message])
        subprocess.run(["git", "push", "origin", branch])


    def run_trading(self):
        itr = 0
        while True:
            loop_start_time = time.time()

            current_price_data = self.getdata()

            # Show current portfolio information
            display_data = None
            display_data = self.show_current_info(current_price_data)
            #except  : pass

            # Find sell + buy opportunity
            stocks_to_sell, stocks_to_buy, current_valuations = [], [], {}
            stocks_to_sell, stocks_to_buy, current_valuations = self.sell_and_buy(current_price_data)
            #except: pass

            # Execute the trades
            trade_data = None
            try: trade_data = self.execute_trade(stocks_to_sell, stocks_to_buy, current_valuations)
            except: pass

            current_data = display_data + "\n\n\n\n" + trade_data
            current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            with open(f"logs/{current_time_str}.txt", "w") as f:
                f.write(current_data)

            wait_time = int(self.parameters.iteration_time_period - (time.time() - loop_start_time))
            if wait_time > 0:
                for _ in tqdm.tqdm(range(wait_time), desc="Time until next iteration (s)", unit="s"):
                    time.sleep(1) # Ensure we take 60 seconds per iteration
            print()
            print("_________________________________________________________________________________")
            print()

if __name__ == "__main__":
    parameters       = Parameters()
    signal_generator = SignalGenerator(parameters.symbols, parameters)
    signal_generator.start()