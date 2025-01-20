'''
20/1/25: need to modify to include subpages + livecrawl. needs to be defined in the ExaSearchContentsResult, under the 'content' attribute, which itself shd be a dictionary that holds these other methods

'''

from exa_py import Exa
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import os 
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class ExaSearchContentsResult:
    '''Data class for individual search results returned from Exa .search_and_contents() method: https://docs.exa.ai/integrations/python-sdk-specification#returns-example-2 + https://docs.exa.ai/reference/get-contents'''
    url: str
    id: str
    text: str
    highlights: List[str]
    highlight_scores: List[float]
    
    # Optional fields from contents endpoint
    title: Optional[str] = None
    score: Optional[float] = None
    published_date: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    subpages: Optional[List[Dict[str, Any]]] = None  # List of crawled subpages
    error: Optional[str] = None  # Error message if content retrieval failed
    status_code: Optional[int] = None  # HTTP status code from content retrieval

@dataclass
class ExaSearchResponse:
    '''Data class for the complete search_contents response (list of results) including metadata'''
    results: List[ExaSearchContentsResult]
    resolved_search_type: Optional[str]

class ExaSearchClient:
    '''Client for executing Exa searches and parsing responses'''

    def __init__(self, api_key: Optional[str] = None):
        '''Initialize the exa client with an API key. If no key is provided, attempts to load from environment variables.'''
        if api_key is None:
            root_dir = Path(__file__).resolve().parent.parent
            env_path = root_dir / '.env'
            load_dotenv(env_path)
            api_key = os.getenv('EXA_API_KEY')
        
            if not api_key:
                raise ValueError("No API key provided and EXA_API_KEY not found in env variables")

        self.exa = Exa(api_key)
    
    def execute_search(
            self,
            query: str,
            num_results: int = 5,
            highlight_query: str = 'Key points',
            highlight_count: int = 1,
            summary_query: str = 'Main points'
    ) -> ExaSearchResponse:
        '''
        Execute a search using Exa API and return parsed results
        
        Args:
            query: search query string
            num_results: number of results to return
            highlight_query: query to use for generating highlights
            highlight_count: number of highlights per URL
            summary_query: query to use for generating summary

        Returns:
            parsed ExaSearchResponse object
        
        '''
        raw_response = self.exa.search_and_contents(query,
                                                    type='auto',
                                                    use_autoprompt=True,
                                                    highlights={
                                                        'numSentences': 1,
                                                        'highlightsPerUrl': highlight_count,
                                                        'query': highlight_query
                                                    },
                                                    summary={
                                                        'query': summary_query
                                                    },
                                                    num_results=num_results
                                                    )

        return self.parse_response(raw_response)
    
    def parse_response(self, response) -> ExaSearchResponse:
        '''
        Parse Exa SearchResponse return object into our structured data class
        
        Args:
            response: Raw SearchResponse object from Exa API, list of results
            
        Returns:
            ExaSearchResponse object containing parsed data
        '''
        parsed_results = []

        for result in response.results:
            parsed_result = ExaSearchContentsResult(
                # required fields
                url=result.url,
                id=result.id,
                text=result.text,
                highlights=result.highlights,
                highlight_scores=result.highlight_scores,

                # optional fields
                title=getattr(result, 'title', None),
                score=getattr(result, 'score', None),
                published_date=getattr(result, 'published_date', None),
                author=getattr(result, 'author', None),
                content=getattr(result, 'content', None),
                summary=getattr(result, 'summary', None),
                subpages=getattr(result, 'subpages', None),
                error=getattr(result, 'error', None),
                status_code=getattr(result, 'status_code', None)
            )
            parsed_results.append(parsed_result)
        
        return ExaSearchResponse(
            results=parsed_results,
            resolved_search_type=getattr(response, 'resolved_search_type', None)
        )
    
    def to_dict(self, response: ExaSearchResponse) -> Dict:
        '''
        Convert ExaSearchResponse to dictionary format
        
        Args:
            response: ExaSearchResponse object
        
        Returns:
            dictionary representation of the response
        '''
        return {
            'results': [asdict(result) for result in response.results],
            'resolved_search_type': response.resolved_search_type
        }
    
if __name__ == "__main__":
    client = ExaSearchClient()

    search_response = client.execute_search(
        query="Here's the top 5 startups working in DNA sequencing",
        num_results=5,
        #? can also define highlights query and summary query
    )

    # access parsed data
    print(f"Search type: {search_response.resolved_search_type}")
    print(f"Found {len(search_response.results)} results")
    for result in search_response.results:
        print(f"\nTitle: {result.title}")
        print(f"URL: {result.url}")
        print("Summary:", result.summary)
        print("Highlights:")
        for highlight, score in zip(result.highlights, result.highlight_scores):
            print(f"- {highlight} (score: {score})")
        if result.subpages:
            print(f"Number of subpages: {len(result.subpages)}")