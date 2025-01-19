# Life Path Generator

a roadmap generator that will create and _learn from your profile_, to generate an entire curriculum for anything that you want to achieve in life !

- will scrape from your bookmarks, youtube likes, twitter feed, etc. to generate learning curriculum tailored to you
- will have gamified checkpoints that will reflect your progress, allow feedback on how the course is structured so far, allow you to fork in a different direction, etc.
- will break down into stages of progression, such that at different stages the kinds of resources change and scale

## Differentation

there are other products out there, but none look polished enough or sufficiently tailored to the individual.

my edge will be really silo-ing in unto user's profiles, creating a knowledge profile of them that will feel haptic and intuitive, and therefore pushing forward with a truly customised curriculum builder.

the premiums that i could therefore charge from this could be incredible.

### Potential trade-offs

perhaps a trade-off I will eventually have to make is whether or not to pivot into focusing on very specific niche curriculum builder types, since such an open-ended product could end up becoming diluted and heavy-footed, instead of adept and dexterous. We shall see down the line.

## Pipeline / tech stack:

user prompt
--> exa AI will ingest it, return the top most meaningful links from its neural web search

--> our custom RAG agent will scrape those top most relevant links, and return the docs / resources in them that are most valuable (crawl4AI, pydanticAI, etc.)

--> will start structuring the curriculum based on these resources and build a roadmap for you

the base conceit here is that our data in the diff platforms + bookmarks + search history are an innate database of our preferences, biases, likes and desires. This is meant to ingest them, feed it into a neural system, and make it come alive -- except now, instead of predicting the next word, its to predict the next action we should take in the quest to become `xyz`.

## Next steps:

19/1/25: - look into pydantic AI, seems like it does a lot of the agent creation under the hood for us extremely conveniently !
