from pydantic import BaseModel, Field
from typing import List, Optional, Dict, TypedDict
import datetime

class FinancialState(TypedDict):
    """Represents the state of our financial data retrieval process."""
    question: str
    tickers: List[str]
    company_data: Dict[str, "CompanyData"]

# A Pydantic model to define the structure of the data we expect from the LLM.
class TickerList(BaseModel):
    """A list of stock ticker symbols."""
    tickers: List[str] = Field(description="A list of valid stock ticker symbols found in the user's question.")

# A Pydantic model to define the structure for a single company's data.
class CompanyData(BaseModel):
    """Holds financial data for a single company."""
    last_updated: str = None
    price_to_earnings: float | None = Field(default=None, alias="forwardPE")
    price_to_book: float | None = Field(default=None, alias="priceToBook")
    earning_per_share: float | None = Field(default=None, alias="revenuePerShare")
    overall_sentiment: str = "Sentiment analysis not performed yet."