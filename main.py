from competitive_analysis_gpt.functions import (
    ScrapeURL,
    ScrapeURLs,
    GetCrunchbaseFinancials,
    GoogleSearch,
    GoogleSearches,
    GetYoutubeTranscript,
    ResearchComplete,
)
from competitive_analysis_gpt.prompts import SYSTEM_PROMPT_V1, SYSTEM_PROMPT_V2, SYSTEM_PROMPT_V3
from competitive_analysis_gpt.agent_runner import AgentRunner
from competitive_analysis_gpt.llm_util import GPT4, GPT35
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import pandas as pd


MAX_NUM_STEPS = 20


def run(query, model):
    c = AgentRunner(
        functions=[
            ScrapeURL,
            GoogleSearch,
            GetYoutubeTranscript,
            ResearchComplete,
        ],
        model=model,
    )
    c.add_message("system", SYSTEM_PROMPT_V3)
    c.add_message("user", query)
    complete = False
    num_steps = 0
    conversation_index = 0
    while not c.complete:
        c.chat_completion_with_function_execution(force_complete=num_steps >= MAX_NUM_STEPS)
        num_steps += 1
        c.display_conversation(conversation_index)
        conversation_index = len(c.conversation_history)

    return c


def get_input():
    print("Enter the company urls (preferred) or names one line at at time:")
    names = []
    while True:
        name = input()
        if name == "":
            break
        names.append(name)

    guidance_keywords = input(
        "Enter any guidance keywords to improve search (comma separated, press Enter if none): "
    ).split(",")
    guidance_keywords = [keyword.strip() for keyword in guidance_keywords if keyword.strip()]

    return names, guidance_keywords


def main():
    company_names, guidance_keywords = get_input()
    results = []
    for company in company_names:
        if not company.strip():
            continue
        company_user_prompt = json.dumps({"company_name": company, "keywords": guidance_keywords})
        print("=" * 100)
        print(company)
        c = run(company_user_prompt, GPT4)
        final_response = c.final_response
        results.append(final_response["company_profile"])
        results[-1]["company_name"] = company
        results[-1]["remaining_tasks"] = final_response["remaining_tasks"]
        print("=" * 100)

    df = pd.DataFrame(results)
    df.to_csv("results.csv", index=False)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
