from pydantic import BaseModel, Field
from typing import List, Optional
import datetime


class TinkerData(BaseModel):
    ticker: str



class FinancialSentimentAnalysis(BaseModel):
    tinker: str
    overall_sentiment: str = Field(description="The overall mood of investors of the specific asset")


class FinancialComparison(BaseModel):
    """Comparative analysis of two or more companies."""
    company_a_name: str
    company_b_name: str
    revenue_comparison: str = Field(
        description="A detailed comparison of revenue growth for both companies over the specified period.")
    key_metrics_comparison: str = Field(
        description="Comparison of key financial metrics (e.g., P/E ratio, market cap).")
    recommendation: Optional[str] = Field(description="A final recommendation or conclusion based on the analysis.")
