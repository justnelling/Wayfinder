# Life Path Generator

a roadmap generator that will create and _learn from your profile_, to generate an entire curriculum for anything that you want to achieve in life !

- will scrape from your bookmarks, youtube likes, twitter feed, etc. to generate learning curriculum tailored to you
- will have gamified checkpoints that will reflect your progress, allow feedback on how the course is structured so far, allow you to fork in a different direction, etc.
- will break down into stages of progression, such that at different stages the kinds of resources change and scale

## Fundamental questions to ask (field its in, space for a pivot)

1. this takes us from a user already knowing what they want. What if they don't know? or are uninspired and stuck? --> What if we could create the ultimate most generalist "writer's block" solution to general uninspired-ness app?

2. I'm working on parsing structured data + consolidating a really haptic user profile to feed into a web search --> could this more generally be a refined web search solution?

## Competitors

https://www.airoadmapgenerator.com/roadmap/cm5prf2d90001dancj85l382m

    i like how they immediately graphify it, and it becomes a tree that breaks down the task into iterative learning steps

## Differentation

there are other products out there, but none look polished enough or sufficiently tailored to the individual.

my edge will be really silo-ing in unto user's profiles, creating a knowledge profile of them that will feel haptic and intuitive, and therefore pushing forward with a truly customised curriculum builder.

the premiums that i could therefore charge from this could be incredible.

### Potential trade-offs

perhaps a trade-off I will eventually have to make is whether or not to pivot into focusing on very specific niche curriculum builder types, since such an open-ended product could end up becoming diluted and heavy-footed, instead of adept and dexterous. We shall see down the line.

## Pipeline / tech stack:

user prompt
--> exa AI will ingest it, return the top most meaningful links from its neural web search

--> our custom RAG agent will scrape those top most relevant links, and return the docs / resources in them that are most valuable (crawl4AI, pydanticAI, etc.) \* exa has get_contents API that can crawl pages / subpages of links too

--> will start structuring the curriculum based on these resources and build a roadmap for you

the base conceit here is that our data in the diff platforms + bookmarks + search history are an innate database of our preferences, biases, likes and desires. This is meant to ingest them, feed it into a neural system, and make it come alive -- except now, instead of predicting the next word, its to predict the next action we should take in the quest to become `xyz`.

### Crawling subpages

both exa and crawl4ai allow for crawling subpages, but at least as of 20/01/25, crawl4ai's crawling of webpages using the sitemaps generated from `{url}/sitemap.xml` seems more robust.
see (crawl4AI/starter_examples/2_crawl_multi_page.py) vs https://docs.exa.ai/reference/crawling-subpages-with-exa

\*\* note not all websites will have `/sitemap.xml` nor `/robots.txt` defined. So for those instances, we should use `exa.ai`'s crawler to crawl the subpages

### Real-time crawling

Exa AI's LiveCrawl will give the most updated crawl version, because otherwise Exa uses cached versions of webpages: https://docs.exa.ai/reference/should-we-use-livecrawl

### Build the user's profile more invasively / profoundly

by scraping their social media, asking them what other interests might bisect with this current lifequest, their life history, etc.

### Git version tracking of the user's progress

and the ability to fork to different paths
