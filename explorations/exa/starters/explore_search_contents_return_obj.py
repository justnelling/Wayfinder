from exa_py import Exa
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List
import json
from dataclasses import dataclass, asdict
from pprint import pprint

@dataclass
class ParsedExaResult:
    title: str
    url: str
    text: str
    highlights: str
    summary: str
    
class ExaResponseExplorer:
    def __init__(self, api_key: str):
        self.exa = Exa(api_key)
    
    def explore_response_structure(self, search_result) -> None:
        """
        Print out the structure and available attributes of the search response
        """
        print("\n=== Exploring Exa Response Structure ===")
        
        # Get all attributes
        attributes = dir(search_result)
        print("\nAvailable attributes:")
        for attr in attributes:
            if not attr.startswith('_'):  # Skip private attributes
                print(f"- {attr}")
                
        # Explore results attribute specifically
        if hasattr(search_result, 'results'):
            print("\nExploring first result structure:")
            first_result = search_result.results[0]
            result_attrs = dir(first_result)
            for attr in result_attrs:
                if not attr.startswith('_'):
                    try:
                        value = getattr(first_result, attr)
                        print(f"  {attr}: {type(value)}")
                    except Exception as e:
                        print(f"  {attr}: Error accessing - {str(e)}")
    
    def parse_results(self, search_result) -> List[ParsedExaResult]:
        """
        Parse Exa search results into a serializable format
        """
        parsed_results = []
        
        for result in search_result.results:
            parsed_result = ParsedExaResult(
                title=getattr(result, 'title', ''),
                url=getattr(result, 'url', ''),
                text=getattr(result, 'text', ''),
                highlights=getattr(result, 'highlights', ''),
                summary=getattr(result, 'summary', '')
            )
            parsed_results.append(parsed_result)
            
        return parsed_results
    
    def to_dict(self, parsed_results: List[ParsedExaResult]) -> List[Dict]:
        """
        Convert parsed results to dictionary format
        """
        return [asdict(result) for result in parsed_results]
    
    def perform_search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform search and return parsed results
        """
        result = self.exa.search_and_contents(
            query,
            type='auto',
            use_autoprompt=True,
            num_results=num_results,
            highlights={
                "numSentences": 1,
                "highlightsPerUrl": 1,
                "query": "Key advancements"
            },
            summary={"query": "Main developments"}
        )
        
        # Explore the structure
        self.explore_response_structure(result)
        
        # Parse and return results
        parsed_results = self.parse_results(result)
        return self.to_dict(parsed_results)

# Usage example
if __name__ == "__main__":
    # Load environment variables
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / '.env'
    load_dotenv(env_path)
    
    # Initialize explorer
    explorer = ExaResponseExplorer(os.getenv('EXA_API_KEY'))
    
    # Perform search and get parsed results
    results = explorer.perform_search('Here\'s the top 5 startups working in dna sequencing')
    
    # Print parsed results
    print("\n=== Parsed Results ===")
    pprint(results)