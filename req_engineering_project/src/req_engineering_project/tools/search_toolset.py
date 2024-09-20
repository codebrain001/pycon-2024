import os

from crewai_tools import (
    SerperDevTool,
    WebsiteSearchTool,
)
from langchain_community.utilities import ArxivAPIWrapper

# Update with your API keys
# Load environment variables
os.environ["SERPER_API_KEY"] = "xxxx"
os.environ["COMPOSIO_API_KEY"] = "xxxx"

from composio_crewai import Action, ComposioToolSet
composio_toolset = ComposioToolSet()


from crewai_tools import BaseTool

class SearchToolset:
    """
    Manages Google and website search tools.
    """

    def __init__(self):
        """
            Initializes the search tools.
        """
        self.google_search_tool = self.google_search_tool()
        self.website_search_tool = self.website_search_tool()

    def google_search_tool(self):
        """
            Returns an instance of SerperDevTool for general search.
        """
        return SerperDevTool()

    def website_search_tool(self):
        """
        Returns a WebsiteSearchTool for semantic website content search.
        """
        return WebsiteSearchTool()
    
    
class PerplexitySearchTool(BaseTool):
    name: str = "Perplexity AI Search Tool"
    description: str = "Executes queries using Perplexity AI for AI-driven information retrieval."

    def _run(self) -> str:
        """
            Runs a Perplexity AI search
        """
        perplexity_ai_search_tool = composio_toolset.get_tools(
            actions=[Action.PERPLEXITYAI_PERPLEXITY_AI_SEARCH]
        )
        return perplexity_ai_search_tool

class ArxivSearchTool(BaseTool):
    name: str = "Arxiv Research Search Tool"
    description: str = "Searches arXiv for research papers."

    def _run(self, argument: str) -> str:
        """
            Runs an arXiv search with the given query
        """
        arxiv =  ArxivAPIWrapper()
        search_result = arxiv.run(argument)
        return search_result  

    
    
        
       