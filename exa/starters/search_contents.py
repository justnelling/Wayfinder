from exa_py import Exa
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import inspect

root_dir = Path(__file__).resolve().parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

exa = Exa(os.getenv('EXA_API_KEY'))

# result = exa.search_and_contents(
#     'Here\'s the top 5 startups working in dna sequencing',
#     type='auto', # auto, keyword, neural (auto will route for us automatically)
#     use_autoprompt=True, # automatic query optimization
#     num_results=5,
#     highlights={
#         "numSentences": 1,
#         "highlightsPerUrl": 1,
#         "query": "Key advancements"
#     },
#     summary={"query": "Main developments"},
#     # text=True, # if you want the whole page content returned
#     # category='personal site', #* company, research paper, news, pdf, github, tweet, personal site, linkedin profile, financial report 
# )

# Print method signature
print("\nMethod signature:")
print(inspect.signature(exa.search_and_contents))

# Get the source code if available
try:
    print("\nSource code:")
    print(inspect.getsource(exa.search_and_contents))
except TypeError:
    print("Source code not available (might be a built-in or binary module)")

# Get the doc string directly
print("\nDocstring:")
print(exa.search_and_contents.__doc__)

# Print all attributes of the method
print("\nMethod attributes:")
for attr in dir(exa.search_and_contents):
    if not attr.startswith('__'):  # Skip magic methods
        try:
            print(f"{attr}: {getattr(exa.search_and_contents, attr)}")
        except AttributeError:
            print(f"Could not access {attr}")

    