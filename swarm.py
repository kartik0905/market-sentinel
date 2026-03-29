import os
import json
import sys
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.3
)


def fetch_hackernews_top_stories(num_stories=10):
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(top_stories_url, timeout=10)
    story_ids = response.json()[:num_stories]

    stories = []
    for story_id in story_ids:
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        item_response = requests.get(item_url, timeout=10)
        item = item_response.json()
        if item and item.get("title"):
            stories.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "score": item.get("score", 0),
                "by": item.get("by", ""),
                "type": item.get("type", "")
            })
    return stories


raw_stories = fetch_hackernews_top_stories(10)
stories_text = json.dumps(raw_stories, indent=2)

osint_fetcher = Agent(
    role="OSINT Fetcher",
    goal="Collect and summarize the latest top stories from HackerNews for competitive intelligence analysis.",
    backstory="You are a specialist in open-source intelligence gathering. You monitor tech news feeds and extract relevant signals for strategic analysis.",
    llm=llm,
    verbose=False,
    allow_delegation=False
)

signal_analyzer = Agent(
    role="Signal Analyzer",
    goal="Categorize technology news stories into Threats, Opportunities, or Trends for a competitive intelligence report.",
    backstory="You are a senior competitive intelligence analyst. You examine raw tech news and classify each item based on its strategic implications for a technology company.",
    llm=llm,
    verbose=False,
    allow_delegation=False
)

strategy_writer = Agent(
    role="Strategy Writer",
    goal="Produce a structured JSON intelligence report with threats, opportunities, and trends arrays.",
    backstory="You are a strategic report writer who transforms categorized intelligence signals into clean, actionable JSON reports for executive consumption.",
    llm=llm,
    verbose=False,
    allow_delegation=False
)

fetch_task = Task(
    description=f"""Here are the latest top stories fetched from HackerNews:

{stories_text}

Summarize each story in one sentence, noting the title, score, and URL. Present them as a numbered list.""",
    expected_output="A numbered list of summarized HackerNews stories with title, score, and URL for each.",
    agent=osint_fetcher
)

analyze_task = Task(
    description="""Take the summarized HackerNews stories from the previous task and categorize each one into exactly one of these three categories:

1. "Threats" - Stories about competitors gaining ground, new disruptive technologies, regulatory risks, or security vulnerabilities.
2. "Opportunities" - Stories about emerging markets, new tools/frameworks to adopt, partnership possibilities, or underserved niches.
3. "Trends" - Stories about general industry movements, developer sentiment shifts, or technology adoption patterns.

For each story, provide the original title, the category, and a one-sentence rationale for the classification.""",
    expected_output="A categorized list of stories, each with a title, category (Threat/Opportunity/Trend), and rationale.",
    agent=signal_analyzer
)

strategy_task = Task(
    description="""Take the categorized intelligence from the previous task and format it as a strict JSON object with this exact structure:

{
  "threats": [
    {"title": "...", "rationale": "..."}
  ],
  "opportunities": [
    {"title": "...", "rationale": "..."}
  ],
  "trends": [
    {"title": "...", "rationale": "..."}
  ]
}

Rules:
- Output ONLY the JSON object, nothing else.
- No markdown formatting, no code fences, no explanatory text.
- Every story must appear in exactly one category.
- Each entry must have "title" and "rationale" fields.""",
    expected_output='A raw JSON object with "threats", "opportunities", and "trends" arrays.',
    agent=strategy_writer
)

crew = Crew(
    agents=[osint_fetcher, signal_analyzer, strategy_writer],
    tasks=[fetch_task, analyze_task, strategy_task],
    process=Process.sequential,
    verbose=False
)

result = crew.kickoff()

raw_output = str(result)

try:
    start = raw_output.index("{")
    end = raw_output.rindex("}") + 1
    json_str = raw_output[start:end]
    parsed = json.loads(json_str)
except (ValueError, json.JSONDecodeError):
    parsed = {
        "threats": [],
        "opportunities": [],
        "trends": []
    }

if "threats" not in parsed:
    parsed["threats"] = []
if "opportunities" not in parsed:
    parsed["opportunities"] = []
if "trends" not in parsed:
    parsed["trends"] = []

print(json.dumps(parsed))
