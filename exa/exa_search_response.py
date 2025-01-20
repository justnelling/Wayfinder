from exa_py import Exa
from dataclasses import dataclass, asdict
from typing import List, Optional, Union, Dict, Any, Literal
import os
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class SearchOptions:
    """All available search and content options for Exa API"""
    # Required content parameters (with defaults)
    text: Union[Dict[str, Any], Literal[True]] = True
    highlights: Union[Dict[str, Any], Literal[True]] = True
    summary: Union[Dict[str, Any], Literal[True]] = True
    
    # Optional search parameters
    num_results: Optional[int] = None
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    start_crawl_date: Optional[str] = None
    end_crawl_date: Optional[str] = None
    start_published_date: Optional[str] = None
    end_published_date: Optional[str] = None
    include_text: Optional[List[str]] = None
    exclude_text: Optional[List[str]] = None
    use_autoprompt: Optional[bool] = None
    type: Optional[str] = None
    category: Optional[str] = None
    
    # Crawling options
    livecrawl_timeout: Optional[int] = None
    livecrawl: Optional[str] = None  # "always", "fallback", or None
    subpages: Optional[int] = None
    subpage_target: Optional[Union[str, List[str]]] = None
    filter_empty_results: Optional[bool] = None
    
    # Additional options
    extras: Optional[Dict[str, int]] = None
    flags: Optional[List[str]] = None

    def to_api_params(self) -> Dict[str, Any]:
        """Convert options to API parameters"""
        params = {}
        
        # Add all non-None values to params
        for field, value in asdict(self).items():
            if value is not None:
                params[field] = value
        
        return params

@dataclass
class ExaSearchResult:
    """Individual search result"""
    url: str
    id: str
    text: str
    highlights: List[str]
    highlight_scores: List[float]
    title: Optional[str] = None
    score: Optional[float] = None
    published_date: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None

@dataclass
class ExaSearchResponse:
    """Complete search response"""
    results: List[ExaSearchResult]
    resolved_search_type: Optional[str] = None

class ExaSearchClient:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from parameter or environment"""
        if api_key is None:
            root_dir = Path(__file__).resolve().parent.parent
            env_path = root_dir / '.env'
            load_dotenv(env_path)
            api_key = os.getenv('EXA_API_KEY')
            if not api_key:
                raise ValueError("No API key provided and EXA_API_KEY not found in environment")
        self.exa = Exa(api_key)

    def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> ExaSearchResponse:
        """
        Execute search with Exa API
        
        Args:
            query: Search query string
            options: SearchOptions instance with desired parameters
        """
        if options is None:
            options = SearchOptions()
        
        # Get API parameters from options
        params = options.to_api_params()
        
        # Execute search
        response = self.exa.search_and_contents(
            query=query,
            **params
        )

        return self._parse_response(response)

    def _parse_response(self, response) -> ExaSearchResponse:
        """Internal method to parse API response"""
        parsed_results = [
            ExaSearchResult(
                url=result.url,
                id=result.id,
                text=result.text,
                highlights=result.highlights,
                highlight_scores=result.highlight_scores,
                title=getattr(result, 'title', None),
                score=getattr(result, 'score', None),
                published_date=getattr(result, 'published_date', None),
                author=getattr(result, 'author', None),
                summary=getattr(result, 'summary', None),
                error=getattr(result, 'error', None),
                status_code=getattr(result, 'status_code', None)
            )
            for result in response.results
        ]
        
        return ExaSearchResponse(
            results=parsed_results,
            resolved_search_type=getattr(response, 'resolved_search_type', None)
        )

# Example usage
if __name__ == "__main__":
    client = ExaSearchClient()
    
    # Basic usage with defaults
    # basic_response = client.search(
    #     query="Latest developments in LLM capabilities"
    # )

    # Advanced usage with custom options
    options = SearchOptions(
        text={'max_characters': 300, 'include_html_tags': False},
        highlights={
            'num_sentences': 1,
            'highlights_per_url': 1,
            'query': "Key advancements"
        },
        summary={'query': "Main developments"},
        num_results=5,
        # category="research paper",
        # include_domains=["arxiv.org"],
        # start_published_date="2023-01-01T00:00:00.000Z",
        # livecrawl="always",
        # extras={'links': 1, 'image_links': 1}
    )
    
    advanced_response = client.search(
        query="The top 5 hottest AI startups out now",
        options=options
    )

    # Print results
    print(f"SEARCH TYPE: {advanced_response.resolved_search_type}")
    for result in advanced_response.results:
        print(f"\nTitle: {result.title}")
        print(f"URL: {result.url}")
        print(f"Summary: {result.summary}")
        print(f"Text: {result.text}")
        for highlight, score in zip(result.highlights, result.highlight_scores):
            print(f"- {highlight} (score: {score})")