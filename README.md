# Competitive Analysis GPT

Competitive Analysist GPT is an LLM agent that performs competitive analysis for tech startups.

Generate a spreadsheet from a list of company names within minutes with the following columns:

- use cases
- target customer profile
- features
- integrations
- investor names
- investor leads
- founded date

Craefully designed to get the job done effectively.

Requires a single OpenAI API Key to get started.

## Demo Video
https://github.com/rohankshir/CompetitiveAnalysisGPT/assets/2716590/e458fa2d-d213-43da-80fc-86e28a4e3c5f


This could be a useful starting point for start ups building new products, vendor analysis, and VC scouting / due diligence.

## Features

- Focuses primarily on the company website, crunchbase, ycombinator before deferring to google
- Runs in your terminal but dead simple to integrate within a service (Flask, FastAPI) or a bot (Slack, Teams)
- Live streaming action log of the decisions the agent is making
- Returns a remaining task list of information it wasn't able to find
- No infinite agent loops - Set the max number of turns per agent
- Uses multiple agent runs to stay within the 32K Context Window
- Easy to understand code and prompts - No Langchain.

## Average Timing and Cost **per** Company

Time: ~1 minute
Cost: 1 USD

## Installation

This project uses Poetry for dependency management. Make sure you have [Poetry installed](https://python-poetry.org/docs/#installation), and then you can install the dependencies by running:

```bash
poetry install
```

If you don't have poetry, you can use whichever Python Env Manager you want, setup a 3.10+ Python Env, and install from `requirements.txt`

You also need the following environment variables set:

```
OPENAI_API_KEY=your-api-key
```

Make sure to replace the values with your actual information.

**Note: Make sure you have access to gpt-4-32k**

## Command Line Usage

After installing the dependencies and setting up the .env file, you can run the project using:

```
poetry run python main.py
```

Enter one company name or URL per line, and hit enter again when you're done.
Optionally add any guidance keywords to help the agent search better and find good URLs.

Output: `result.csv` in your current working directory

## Slack Usage

1. Create a slack app in your workspace using [`slack_manifest.yaml`](./slack_manifest.yaml)
2. Source all relevant env vars (reference [.env.template](./.env.template)) into your environment
3. `poetry run python slack.py`
4. In Slack, add Competitive Analysis GPT to a Slack channel and mention it to begin.

## Contributing

Contributions are welcome!
Steps:

1. Create a Github Issue to discuss the enhancement
2. Submit a PR from your forked repo
3. I will review and merge it in!

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Contact

Rohan Kshirsagar - rohan.m.kshirsagar@gmail.com
