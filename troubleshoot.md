# Try Instructor library next instead

so pydanticAI has some intuitive haptics, but is buggy when running anthropic / openrouter + deepseek.

dave ebbelar mentioned using `Instructor` library instead. try that next

# PydanticAI

## Using openrouter + deepseek in the pydanticAI calls

super slow

## Using anthropic API directly in pydanticAI calls

much faster, but there's some issue with tool use input format being incorrect

## Prompter.py test run

(with openai API directly via pydanticAI)

even with the steady state of injected prompts now returning my structured schema data, the LLM hallucinates a lot of information in the required fields -- aka it can guarantee the enum structure but it still hallucinates the content

i'm thinking instead of building the profile through LLM interactions, we minimize this language part as much as possible, and stick to old-fashioned profile input fields in a form.

## then the pipeline can be:

maybe still chat landing page -->

if met with generic prompt:
--> launch profile input form filling page

if met with comprehensive prompt:
--> we try to parse it out with the LLM,

takes the entire comprehensive profile schema + user prompt --> sends it to exa AI neural search API to get the most thorough results
