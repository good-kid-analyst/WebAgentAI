import os
import requests
import matplotlib.pyplot as plt
from langgraph.graph import StateGraph
from langgraph.graph import START, END

from State import State
from dotenv import load_dotenv
from google.genai import Client
import praw


class WebAgent:
    def __init__(self):
        load_dotenv("../config/.env")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = Client(
            api_key=self.api_key,
        )

        reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        reddit_client_secret = os.getenv("REDDIT_SECRET")
        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            redirect_uri="http://localhost:8080",
            user_agent="Karma breakdown 1.0 by /u/riki4284 ",
        )

    @staticmethod
    def google_search(state: State):
        print("Searching Google using SERP...")
        question = state["question"]

        # Use SerpApi or your self-hosted search engine API
        # Replace with your actual SerpApi key and endpoint

        api_key = os.getenv("SERP_KEY")
        url = f"https://serpapi.com/search.json?q={question}&api_key={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            search_results = response.json().get("organic_results", [])
            print(search_results)
            # Extract and format the results for analysis
            summaries = [f"Title: {r['title']}\nSnippet: {r['snippet']}" for r in search_results[:5]]

            return {"google_results": summaries}
        except Exception as e:
            print(f"Google search failed: {e}")
            return {"google_results": []}  # Return empty to handle graceful failure

    def reddit_search(self, state: State):
        print("Searching Reddit for relevant discussions...")
        question = state.get("question")
        results = []
        try:
            # Use the search method to find submissions across all of Reddit
            # You can adjust the subreddit and limit as needed
            for submission in self.reddit.subreddit("all").search(question, limit=5):
                results.append({
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "url": submission.url
                })
                print(results[-1])

            return {"reddit_results": results}

        except Exception as e:
            print(f"Error during Reddit search: {e}")
            # Return an empty list on failure to prevent the graph from crashing
            return {"reddit_results": []}

    def google_analysis(self, state: State):
        pass

    def reddit_analysis(self, state: State):
        pass

    def synthesize_answer(self, state: State):
        pass

    def build_graph(self):
        builder = StateGraph(State)
        # builder.add_node("google-search", self.google_search)
        builder.add_node("reddit-search", self.reddit_search)
        # builder.add_node("google-analysis", self.google_analysis)
        # builder.add_node("reddit-analysis", self.reddit_analysis)
        # builder.add_node("synthesize-answer", self.synthesize_answer)

        # builder.add_edge(START, "google-search")
        builder.add_edge(START, "reddit-search")
        # builder.add_edge("reddit-search", "reddit-analysis")
        # builder.add_edge("google-search", "google-analysis")
        # builder.add_edge("google-analysis", "synthesize-answer")
        # builder.add_edge("reddit-analysis", "synthesize-answer")
        # builder.add_edge("synthesize-answer", END)
        # builder.add_edge("google-search", END)
        builder.add_edge("reddit-search", END)
        graph = builder.compile()

        return graph

    def run(self):
        graph = self.build_graph()
        while True:
            print("Starting WebAgent")
            question = input("What do you want to lookup?")
            initial_state = State(
                messages=[{"role": "user", "content": question}],
                question=question,
                google_results=None,
                reddit_results=None,
            )

            # The .stream() method is better for complex agents as it shows incremental progress
            final_state = {}
            for state in graph.stream(initial_state):
                print(f"Current State: {state}")
                final_state = state

            print("\nFinal Answer:")
            print(final_state.get("final_answer"))


if __name__ == '__main__':
    WebAgent().run()