# Life Path Generator

a roadmap generator that will create and learn from your profile, to generate an entire curriculum for anything that you want to achieve in life !

- will scrape from your bookmarks, youtube likes, twitter feed, etc. to generate learning curriculum tailored to you
- will have gamified checkpoints that will reflect your progress, allow feedback on how the course is structured so far, allow you to fork in a different direction, etc.
- will break down into stages of progression, such that at different stages the kinds of resources change and scale

Pipeline / tech stack:

user prompt
--> exa AI will ingest it, return the top most meaningful links from its neural web search

--> our custom RAG agent will scrape those top most relevant links, and return the docs / resources in them that are most valuable (crawl4AI, pydanticAI, etc.)

--> will start structuring the curriculum based on these resources and build a roadmap for you

the base conceit here is that our data in the diff platforms + bookmarks + search history are an innate database of our preferences, biases, likes and desires. This is meant to ingest them, feed it into a neural system, and make it come alive -- except now, instead of predicting the next word, its to predict the next action we should take in the quest to become `xyz`.
