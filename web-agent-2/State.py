from typing import TypedDict, List
from typing_extensions import Annotated
from langgraph.graph import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    question: str | None
    google_results: str | None
    reddit_results: str | None

