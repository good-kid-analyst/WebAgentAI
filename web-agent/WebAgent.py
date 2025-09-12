from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph
from State import (OverallState,
                   QueryGenerationState,
                   ReflectionState,
                   WebSearchState)
from Configuration import Configuration
from langchain_core.runnables import RunnableConfig
from Schema import SearchQueryList
from Prompt import query_writer_instructions, web_searcher_instructions
from Utils import get_research_topic, get_current_date, resolve_urls, get_citations, insert_citation_markers
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END
from argparse import ArgumentParser
from langchain_core.messages import HumanMessage
from google.genai import Client

class WebAgent:
    def __init__(self):
        load_dotenv("../config/.env")
        if os.getenv("GEMINI_API_KEY") is None:
            raise ValueError("GEMINI_API_KEY is not set")
        else:
            self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = Client(
            api_key=self.api_key,
        )
        self.run()

    def load_graph(self):
        builder = StateGraph(OverallState, config_schema=Configuration)
        self.add_node(builder,"generate_query", self.generate_query)
        self.add_node(builder,"web_search", self.search_web)
        self.add_edge(builder, START, "generate_query")
        self.add_edge(builder, "generate_query", "web_search")
        self.add_edge(builder, "web_search", END)
        return builder

    @staticmethod
    def add_node(builder:StateGraph, key, func):
        builder.add_node(key, func)
        return builder

    @staticmethod
    def add_edge(builder: StateGraph, start, end, is_conditional=False):
        if is_conditional:
            builder.add_conditional_edges(start, end)
        else:
            builder.add_edge(start, end)
        return builder

    def generate_query(self, state: OverallState, config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        llm = ChatGoogleGenerativeAI(
            model=configurable.query_generator_model,
            temperature=1.0,
            max_retries=2,
            api_key=self.api_key,
        )
        structured_llm = llm.with_structured_output(SearchQueryList)
        formatted_prompt = query_writer_instructions.format(
            current_date=get_current_date(),
            research_topic=get_research_topic(state["messages"]),
            number_queries=state["initial_search_query_count"],
        )
        result = structured_llm.invoke(formatted_prompt)
        return {"search_query": result.query}

    def search_web(self, state: OverallState, config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        question = state.get("search_query")
        formatted_prompt = web_searcher_instructions.format(
            current_date=get_current_date(),
            research_topic=question,
        )
        response = self.client.models.generate_content(
            model="gemini-1.5-flash",
            contents=formatted_prompt,
            config={
                "tools": [{"google_search_retrieval": {}}],
                "temperature": 0,
            },
        )
        resolved_urls = resolve_urls(
            response.candidates[0].grounding_metadata.grounding_chunks
        )
        # Gets the citations and adds them to the generated text
        citations = get_citations(response, resolved_urls)
        modified_text = insert_citation_markers(response.text, citations)
        sources_gathered = [item for citation in citations for item in citation["segments"]]

        return {
            "sources_gathered": sources_gathered,
            "search_query": [state["search_query"]],
            "web_research_result": [modified_text],
        }

    def run(self):
        """Run the research agent from the command line."""
        parser = ArgumentParser(description="Run the LangGraph research agent")
        parser.add_argument("question", help="Research question")
        parser.add_argument(
            "--initial-queries",
            type=int,
            default=3,
            help="Number of initial search queries",
        )
        parser.add_argument(
            "--max-loops",
            type=int,
            default=2,
            help="Maximum number of research loops",
        )
        parser.add_argument(
            "--reasoning-model",
            default="gemini-1.5-flash",
            help="Model for the final answer",
        )
        args = parser.parse_args()

        state = {
            "messages": [HumanMessage(content=args.question)],
            "initial_search_query_count": args.initial_queries,
            "max_research_loops": args.max_loops,
            "reasoning_model": args.reasoning_model,
        }
        builder = self.load_graph()
        graph = builder.compile(name="search-agent")
        result = graph.invoke(state)
        messages = result.get("messages", [])
        if messages:
            print(messages[-1].content)

if __name__ == '__main__':
    WebAgent()
