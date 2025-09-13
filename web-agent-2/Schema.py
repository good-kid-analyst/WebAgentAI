from typing import List

from pydantic import BaseModel, Field

class GoogleResults(BaseModel):
    sources: List[str] = Field(
        description="List of sources returned by the Google search",
        examples=["https://google.com", "https://www.wikipedia.com"],
    )


class RedditResults(BaseModel):
    subreddits: List[str] = Field(
        description="List of subreddits returned by the Reddit API",
    ),
    comments: List[str] = Field(
        description="List of comments returned by the Reddit API",
    )

