// deno imports
import Exa from "npm:exa-js";
import OpenAI from "npm:openai";

const EXA_API_KEY = "02f84e73-f24e-4215-b1b3-8020de59a706";
const OPENAI_API_KEY =
  "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";

const exa = new Exa(EXA_API_KEY);
const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

async function getLLMResponse({
  system = "You are a helpful assistant.",
  user = "",
  temperature = 1,
  model = "gpt-3.5-turbo",
}) {
  const completion = await openai.chat.completions.create({
    model,
    temperature,
    messages: [
      { role: "system", content: system },
      { role: "user", content: user },
    ],
  });
  return completion.choices[0].message.content;
}

// exa has 2 types of search: neural / keyword

// create helper function to generate search queries for our topic
async function generateSearchQueries(topic, n) {
  const userPrompt = `I'm writing a research report on ${topic} and need help coming up with diverse search queries.
Please generate a list of ${n} search queries that would be useful for writing a research report on ${topic}. These queries can be in various formats, from simple keywords to more complex phrases. Do not add any formatting or numbering to the queries.`;

  const completion = await getLLMResponse({
    system:
      "The user will ask you to help generate some search queries. Respond with only the suggested queries in plain text with no extra formatting, each on its own line.",
    user: userPrompt,
    temperature: 1,
  });
  return completion
    .split("\n")
    .filter((s) => s.trim().length > 0)
    .slice(0, n);
}

// function that calls Exa API to perform searches using Auto search
async function getSearchResults(queries, linksPerQuery = 2) {
  let results: any[] = [];
  for (const query of queries) {
    const searchResponse = await exa.searchAndContents(query, {
      numResults: linksPerQuery,
      useAutoPrompt: false,
    });
    results.push(...searchResponse.results);
  }
  return results;
}

// final step: instruct LLm to synthesize content into a research report
async function synthesizeReport(topic, searchContents, contentSlice = 750) {
  const inputData = searchContents
    .map(
      (item) =>
        `--START ITEM--\nURL: ${item.url}\nCONTENT: ${item.text.slice(
          0,
          contentSlice
        )}\n--END ITEM--\n`
    )
    .join("");
  return await getLLMResponse({
    system:
      "You are a helpful research assistant. Write a report according to the user's instructions.",
    user:
      "Input Data:\n" +
      inputData +
      `Write a two paragraph research report about ${topic} based on the provided information. Include as many sources as possible. Provide citations in the text using footnote notation ([#]). First provide the report, followed by a single "References" section that lists all the URLs used, in the format [#] <url>.`,
    //model: 'gpt-4' //want a better report? use gpt-4 (but it costs more)
  });
}

// wrap everything into 1 Researcher function
async function researcher(topic) {
  console.log(`Startin research on topic: ${topic}`);

  const searchQueries = await generateSearchQueries(topic, 3);
  console.log(`Generated search queries: ${searchQueries}`);

  const searchResults = await getSearchResults(searchQueries);
  console.log(
    `Found ${searchResults.length} search results. here's the first one: ${searchResults[0]}`
  );

  console.log("Synthesizing report...");
  const report = await synthesizeReport(topic, searchResults);

  return report;
}

// lets call the researcher function on our topics
const SAMA_TOPIC = "Sam Altman";
const ART_TOPIC = "renaissance art";

async function runExamples() {
  console.log("Researching Sam Altman:");
  const samaReport = await researcher(SAMA_TOPIC);
  console.log(samaReport);

  console.log("\n\nResearching renaissance art:");
  const artReport = await researcher(ART_TOPIC);
  console.log(artReport);
}

runExamples();
