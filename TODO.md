## Next steps:

_GLOBAL IMPROVEMENTS_
touchup: need to tweak the pathway_generator system prompt to adopt jeremy howard's learning styles principles, but also tailor it to the user profile's learning style i think.

_10/2/25_
frontend UI integration carried by claude. need to test end to end with real LLM pathway data instead of the current `/test` endpoint, and also change the visual formatting cause its really ugly. YAY!

_8/2/25_

next steps: build this into an API backend and then create the frontend

consolidated all the scripts into /src dir as root dir (for python sys path)

/prompt_refinement/prompter.py:

&emsp;- starts the chat_flow(), which constructs user profile through chat

/prompt_refinement/pathway_generator:

&emsp;- now takes in the profile from `prompter.py`, and will feed it to LLM again to generate a curriculum
&emsp;- curriculum follows a tree structure, with 3 levels
&emsp;- each node in tree contains a continuation prompt which is what we feed into `profile_search.py` to get the exa web results

/exa_search/profile_search:

&emsp;- now takes in the continuation query from prompt_refinement/pathway_generator.py
&emsp;- exa API requests look good, just the 'response.text' field sometimes reads in gibberish

_3/2/25_

ok next steps: have to experiment with different user profile types, and see how long it takes for different AI models to respond as well as the quality of the responses.

test how the new pathway_generator works.

if we can verify that it always deterministically generates at least 3 layers of learning pathway tree, then next stretch goal is to figure out a function to extend that depth infinitely, or if its reached the local maxima of what can be learnt in that pathway, suggest next actions

---- DONE ----

now we need to finetune our continuation prompt for each of the subnodes in `pathway_generator.py` because that really needs to do 2 things:

1. inherit from the original richness of the user profile
2. but also narrow down to that specific node in the learning path so the results from Exa AI are super precise and rich!

---- DONE ----
ok now we have user profile + exa web search parsing.

but i think we need an intermediate logic layer that will pass the user profile to an LLM, with the express purpose of getting it to create a learning pathway curriculum (tree-like structure, like in https://www.airoadmapgenerator.com/roadmap/cm5prf2d90001dancj85l382m), and then within each node more specifically it will look up the relevant resources, which will be even more hyper-focused and targeted

_2/2/25_

task now is to figure out how to map our user profile unto exa AI search API to get a truly tailored search request

_1/2/25_

define toolcall that will evaluate for profile completeness

start exploring how to pass this 'full' profile into exa AI

_26/1/25:_

#### Getting structured output in UserProfile correctly

`prompter.py`: with pydanticAI is still kinda wonky, in beta.

try `instructor` library next

our main issue right now is creating the prompt refiner logic with structured output that is:

1. strictly adhered to
2. not hallucinated to fill in the gaps by the LLM (which if you run `prompter.py` rn is what the LLM does)

right now, with pydanticAI + openAI API directly, we get the structured schema back, but its hallucinating its contents.

im thinking instead of getting the UserProfile filled up by the LLM via chat prompt, that we instead get a mix of dynamic + statically generated input fields on a form that correlates to that first prompt that the user sends in.

#### to get structured data, openAI API directly seems promising

https://www.youtube.com/watch?v=fuMKrKlaku4&t=500s

#### Overall pipeline

And it needs to be a very structured pipeline:

![alt text](media/image.png)

#### Setting up the correct chat mechanism

this still WIP: need to study https://ai.pydantic.dev/examples/chat-app/

_20/1/25:_

ok exa api method script pretty much done.

next to build a prompt refiner logic layer, that will ask users targeted questions in trying to build a more cohesive and complete profile of them --> look into pydanticAI

_19/1/25:_

- look into pydantic AI, seems like it does a lot of the agent creation under the hood for us extremely conveniently !
