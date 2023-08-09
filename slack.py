import json
import os
import pandas as pd
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from competitive_analysis_gpt.prompts import SYSTEM_PROMPT_V1, SYSTEM_PROMPT_V2
from competitive_analysis_gpt.agent_runner import AgentRunner
from competitive_analysis_gpt.llm_util import GPT4, GPT35
from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
from competitive_analysis_gpt.functions import (
    ScrapeURL,
    GetCrunchbaseFinancials,
    GoogleSearch,
    GetYoutubeTranscript,
    ResearchComplete,
)
from typing import List, Optional, Dict

MAX_NUM_STEPS = 20


def build_agent(query, model):
    runner = AgentRunner(
        functions=[
            ScrapeURL,
            GoogleSearch,
            GetYoutubeTranscript,
            ResearchComplete,
        ],
        model=model,
    )
    runner.add_message("system", SYSTEM_PROMPT_V2)
    runner.add_message("user", query)
    return runner


app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


def render_json_to_slack(json_data):
    blocks = []
    for key, value in json_data.items():
        if isinstance(value, list):
            value_text = "\n".join(value)
        else:
            value_text = value

        if not value_text:
            value_text = "N/A"

        block = {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*{key}:*"},
                {"type": "mrkdwn", "text": value_text},
            ],
        }
        blocks.append(block)
    return blocks


def render_code(content: Dict, prefix: str):
    result = f"{prefix}\n\n```{json.dumps(content, indent=2)}\n```\n\n"
    return result


@app.event("app_mention")
async def command_handler(body, say, client, logger):
    event = body["event"]
    user = event["user"]
    blocks = [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Start Competitive Analysis"},
                    "action_id": "start_competitive_analysis",
                    "value": json.dumps({"user": user}),
                }
            ],
        }
    ]
    await say(blocks=blocks)


@app.action("start_competitive_analysis")
async def handle_start_competitive_analysis(ack, body, client):
    button_dict = json.loads(body["actions"][0]["value"])
    await ack()
    await client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "company_input_modal",
            "private_metadata": json.dumps(
                {
                    "user": button_dict["user"],
                    "channel_id": body["container"]["channel_id"],
                }
            ),
            "title": {"type": "plain_text", "text": "Select section"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Companies*",
                    },
                },
                {
                    "type": "input",
                    "block_id": "companies",
                    "optional": True,
                    "label": {
                        "type": "plain_text",
                        "text": "Enter your company urls or names (one per line)",
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "companies_input",
                        "multiline": True,
                    },
                },
                {
                    "type": "input",
                    "block_id": "guidance_keywords",
                    "optional": True,
                    "label": {
                        "type": "plain_text",
                        "text": "Guidance keywords (such as product area or technology)",
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "guidance_keywords",
                    },
                },
            ],
            "submit": {"type": "plain_text", "text": "Submit"},
        },
    )


@app.view("company_input_modal")
async def handle_uml_submission(ack, body, client):
    private_metadata = json.loads(body["view"]["private_metadata"])
    await ack()  # Acknowledge the view_submission event
    form_values = body["view"]["state"]["values"]
    companies = form_values["companies"]["companies_input"]["value"].split("\n")
    companies = [company for company in companies if company.strip()]
    guidance_keywords = form_values["guidance_keywords"]["guidance_keywords"]["value"]
    response = await client.chat_postMessage(
        text="`In-progress...` Competitive analysis for the following companies: "
        + ", ".join(companies),
        channel=private_metadata["channel_id"],
    )
    results = []
    for company in companies:
        await client.chat_postMessage(
            text=f"Getting information for company: {company} with guidance keywords: {guidance_keywords}",
            channel=private_metadata["channel_id"],
            thread_ts=response["ts"],
        )
        company_user_prompt = json.dumps({"company_name": company, "keywords": guidance_keywords})
        runner = build_agent(company_user_prompt, GPT4)
        while not runner.complete:
            thread_response = await client.chat_postMessage(
                text="`Thinking...`",
                channel=private_metadata["channel_id"],
                thread_ts=response["ts"],
            )
            function, result = runner.chat_completion_with_function_execution()
            print("Function:", function)
            print("Result:", result)
            function_copy = function.copy()
            function_copy["arguments"] = json.loads(function_copy["arguments"])
            if runner.complete:
                break
            text = render_code(function_copy, "Ran:")
            await client.chat_update(
                text=text,
                channel=private_metadata["channel_id"],
                ts=thread_response["ts"],
            )
        final_response = runner.final_response
        result = {
            "company_name": company,
        }
        result.update(final_response["company_profile"])
        result["remaining_tasks"] = final_response["remaining_tasks"]
        results.append(result)

        blocks = render_json_to_slack(final_response["company_profile"])
        await client.chat_postMessage(
            blocks=blocks,
            channel=private_metadata["channel_id"],
            thread_ts=response["ts"],
        )
    await client.chat_update(
        text=f"Finished competitive analysis for: {','.join(companies)}. Uploading CSV",
        channel=private_metadata["channel_id"],
        ts=response["ts"],
    )
    df = pd.DataFrame(results)
    df.to_csv("slack_results.csv", index=False)
    await client.files_upload(
        channels=private_metadata["channel_id"],
        file="slack_results.csv",
        initial_comment="Here are the results of your competitive analysis",
    )


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
