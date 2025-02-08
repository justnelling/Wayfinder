'''
This is the python version of building exa researcher: https://docs.exa.ai/examples/exa-researcher-python

automatically research relevant sources with Exa's `auto search` and synthesizes the information into a reliable report.

'''
import os
import exa_py
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

EXA_API_KEY = os.getenv('EXA_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LLM_model = os.getenv('LLM_MODEL')

exa = exa_py.Exa(EXA_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# create utility function to pass in system + user messages directly, and get the LLM's response as a string back
def get_llm_response(system="You are a helpful assistant.", user='', temperature=1, model=LLM_model):
    completion = openai_client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
    )
    return completion.choices[0].message.content

# define topics of research
SAMA_TOPIC = 'Sam Altman'
ART_TOPIC = 'renaissance art'

'''
Exa has 2 type of seach:
    1) neural search: preferred when query is broad + complex because it lets us retrieve high quality, semantically relevant data. Neural search is especially suitable when a topic is well-known and popularly discussed on the Internet, allowing the machine learning model to retrieve contents which are more likely recommended by real humans
    
    2) keyword search is useful when the topic is specific, local, or obscure.

conveniently, Exa's auto search feature will automatically decide whether to use `keyword` or `neural` search for each query. For example, if a query is a specific person's name, Exa would decide to use keyword search.
'''

# now create helper function to generate search queries for our topic
def generate_search_queries(topic, n):
    user_prompt = f"""I'm writing a research report on {topic} and need help coming up with diverse search queries.
Please generate a list of {n} search queries that would be useful for writing a research report on {topic}. These queries can be in various formats, from simple keywords to more complex phrases. Do not add any formatting or numbering to the queries."""
    
    completion = get_llm_response(
        system='the user will ask you to help generate some search queries. Respond with only the suggested queries in plain text with no extra formatting, each on its own line.',
        user=user_prompt,
        temperature=1
    )

    return [s.strip() for s in completion.split('\n') if s.strip()][:n]

#! function that calls the Exa API to perform searches using auto search
def get_search_results(queries, links_per_query=2):
    results = []
    for query in queries:
        search_response = exa.search_and_contents(query,
                                                  num_results = links_per_query,
                                                  use_autoprompt=False)
        results.extend(search_response.results)
    return results

# function to synthesize the search results into a report
def synthesize_report(topic, search_contents, content_slice=750):
    input_data = '\n'.join([f"--START ITEM--\nURL: {item.url}\nCONTENT: {item.text[:content_slice]}\n--END ITEM--\n" for item in search_contents])
    return get_llm_response(
        system='You are a helpful research assistant. Write a report according to the user\'s instructions.',
        user=f'Input Data:\n{input_data}Write a two paragraph research report about {topic} based on the provided information. Include as many sources as possible. Provide citations in the text using footnote notation ([#]). First provide the report, followed by a single "References" section that lists all the URLs used, in the format [#] <url>.',
        # model='gpt-4'  # want a better report? use gpt-4 (but it costs more)
    )

# all together
def researcher(topic):
    print(f'Starting research on topic: "{topic}"')

    search_queries = generate_search_queries(topic, 3)
    print("Generated search queries:", search_queries)

    search_results = get_search_results(search_queries)
    print(f"Found {len(search_results)} search results. Here's the first one:", search_results[0])

    print("Synthesizing report...")
    report = synthesize_report(topic, search_results)

    return report, search_results

def run_examples():
    print(f"Researching Sam Altman:")
    sama_report, search_results = researcher(SAMA_TOPIC)
    with open(Path(os.getcwd()) / 'exa_researcher' / 'sama_report.txt', 'w', encoding='utf-8') as f:
        f.write(str(search_results))
        f.write(sama_report)

    print("\n\nResearching Renaissance Art:")
    art_report, search_results = researcher(ART_TOPIC)
    with open(Path(os.getcwd()) / 'exa_researcher' / 'art_report.txt', 'w', encoding='utf-8') as f:
        f.write(str(search_results))
        f.write(art_report)

if __name__ == "__main__":
    run_examples()