import os
import requests
import matplotlib.pyplot as plt
from langgraph.graph import StateGraph
from langgraph.graph import START, END

from State import State
from dotenv import load_dotenv
from google.genai import Client
import praw
from langchain_google_genai import ChatGoogleGenerativeAI
from Schema import GoogleResults, RedditResults
from Prompt import synthesise_answer, reflection_instructions
from Utils import current_date

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
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            api_key=self.api_key,
            temperature=1.0,
            max_retries=2,
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
            return {"reddit_results": results}

        except Exception as e:
            print(f"Error during Reddit search: {e}")
            # Return an empty list on failure to prevent the graph from crashing
            return {"reddit_results": []}

    def google_analysis(self, state: State):
        print("Google analysis started...")
        google_results = state.get("google_results")
        user_question = state.get("question")
        llm_structured = self.llm.with_structured_output(GoogleResults)
        formatted_prompt = reflection_instructions.format(
            user_question=user_question,
            search_results=google_results,
        )
        output = llm_structured.invoke(formatted_prompt)
        return {"google_analysis": output}

    def reddit_analysis(self, state: State):
        print("Reddit analysis started...")
        reddit_results = state.get("reddit_results")
        user_question = state.get("question")
        llm_structured = self.llm.with_structured_output(RedditResults)
        formatted_prompt = reflection_instructions.format(
            user_question=user_question,
            search_results=reddit_results,
        )
        output = llm_structured.invoke(formatted_prompt)
        return {"reddit_analysis": output}

    def synthesize_answer(self, state: State):
        print("Get an answer...")
        user_question = state.get("question")
        reddit_res = state.get("reddit_analysis")
        google_res = state.get("google_analysis")
        formatted_prompt = synthesise_answer.format(
            user_question=user_question,
            google_analysis=google_res,
            reddit_analysis=reddit_res
        )
        output = self.llm.invoke(formatted_prompt)
        return {"answer": output.content}

    def build_graph(self):
        builder = StateGraph(State)
        builder.add_node("google-search", self.google_search)
        builder.add_node("reddit-search", self.reddit_search)
        builder.add_node("google-analysis", self.google_analysis)
        builder.add_node("reddit-analysis", self.reddit_analysis)
        builder.add_node("synthesize-answer", self.synthesize_answer)

        builder.add_edge(START, "google-search")
        builder.add_edge("google-search", "reddit-search")
        builder.add_edge("reddit-search", "reddit-analysis")
        builder.add_edge("reddit-analysis", "google-analysis")
        # builder.add_edge("google-analysis", "synthesize-answer")
        # builder.add_edge("reddit-analysis", "synthesize-answer")
        # builder.add_edge("synthesize-answer", END)
        builder.add_edge("google-analysis", "synthesize-answer")
        builder.add_edge("synthesize-answer", END)
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
                google_analysis=None,
                reddit_analysis=None,
                answer=None
            )

            # The .stream() method is better for complex agents as it shows incremental progress
            final_state = {}
            for state in graph.stream(initial_state):
                # print(f"Current State: {state}")
                final_state = state

            print("\nFinal Answer:")
            print(final_state.get("answer"))


if __name__ == '__main__':
    WebAgent().run()