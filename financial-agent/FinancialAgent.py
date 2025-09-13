import datetime
import yfinance as yf
from State import FinancialState, CompanyData
import requests
import asyncio

class Agent:
    def __init__(self, ticker="RACE"):
        #TODO:
        #   - make the functions async
        #   - create llm for sentiment analysis
        self.ticker = ticker
        state = FinancialState(
            question="Retrieve a financial analysis of these companies: Apple, Ferrari",
            tickers=[self.ticker],
        )
        self.ticker_data_retrieval(state)

    @staticmethod
    def get_ticker(company_name):
        print("Retrieving ticker data for {}".format(company_name))
        yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        params = {"q": company_name, "quotes_count": 1, "country": "United States"}

        res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
        try:
            data = res.json()
            company_code = data['quotes'][0]['symbol']
            return company_code
        except Exception as e:
            print("Error retrieving ticker data for {}".format(company_name))
            return None

    @staticmethod
    def fetch_single_ticker_data(ticker: str):
        """Asynchronously fetches data for a single ticker."""
        print(f"Fetching data for {ticker}...")
        try:
            # Use asyncio.to_thread to run the blocking yfinance call concurrently
            ticker_yf = yf.Ticker(ticker)
            info = ticker_yf.info

            # Safely get data, using .get() to handle missing keys
            data = {
                "last_updated": datetime.datetime.fromtimestamp(info["regularMarketTime"]).strftime("%Y-%m-%d"),
                "priceToEarnings": info.get("forwardPE"),
                "priceToBook": info.get("priceToBook"),
                "revenuePerShare": info.get("revenuePerShare"),
            }
            return {"ticker": ticker, "data": data}
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}

    def ticker_data_retrieval(self, state: FinancialState):
        """Node to retrieve stock data concurrently using asyncio."""
        print("Step 2: Retrieving data for all tickers concurrently...")
        tickers = state.get("tickers", [])
        if not tickers:
            print("No tickers found. Skipping data retrieval.")
            return {"company_data": {}}

        results = [self.fetch_single_ticker_data(t) for t in tickers]

        companies_data = {}
        for res in results:
            ticker = res.get("ticker")
            if "error" in res:
                companies_data[ticker] = CompanyData(overall_sentiment=f"Data retrieval failed: {res['error']}")
            else:
                companies_data[ticker] = CompanyData(**res["data"])
        print(companies_data)
        return {"company_data": companies_data}

    def analyze_sentiment(self, state: FinancialState):
        """Node to perform sentiment analysis for each company."""
        print("Step 3: Analyzing sentiment for each company...")
        companies_data = state.get("company_data", {})
        llm = MockLLM()

        for ticker, data in companies_data.items():
            if "Data retrieval failed" not in data.overall_sentiment:
                prompt = f"Analyze the sentiment for {ticker} based on its financial data and public perception."
                sentiment = llm.invoke(prompt)
                data.overall_sentiment = sentiment

        return {"company_data": companies_data}



if __name__ == '__main__':
    Agent()

