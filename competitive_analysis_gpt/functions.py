from competitive_analysis_gpt.commands import browse, crunchbase
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json


GPT4 = "gpt-4-32k-0613"
GPT35 = "gpt-3.5-turbo-16k-0613"


class ScrapeURL(BaseModel):
    """
    Use this function to get the contents of a URL in markdown format with all URLs preserved
    """

    url: str = Field(..., description="the url to scrape")

    def execute(self):
        result = browse.scrape_and_convert_to_markdown(self.url, smart_mode=False)
        return result


class GetCrunchbaseFinancials(BaseModel):
    """
    Use this function to get the financials of a company from crunchbase
    to understand who the investors are.
    """

    url: str = Field(..., description="the crunchbase url of the company to search for")

    def execute(self):
        result = crunchbase.get_crunchbase_financials(self.url)
        result = "\n\n".join(result)
        return result


class GoogleSearch(BaseModel):
    """
    Use this function to search google and get the top results
    """

    company_name: str = Field(..., description="the name of the company to search for")
    keywords: str = Field(..., description="extra keywords to search for")

    def execute(self):
        keywords = self.company_name + " " + self.keywords
        result = browse.search_urls_and_preview(keywords, 10)
        return json.dumps(list(result), indent=2)


class GetYoutubeTranscript(BaseModel):
    """
    Use this function to get the markdownified transcript of a URL from youtube
    """

    url: str = Field(..., description="the url to scrape")

    def execute(self):
        result = browse.get_youtube_transcript(self.url)
        return result


class CompanyProfile(BaseModel):
    """
    All the information you need to know about a company to do competitive research
    """

    one_liner: str = Field(..., description="a one liner about the company")
    founding_date: str = Field(..., description="the date the company was founded")
    use_cases: List[str] = Field(..., description="a list of use cases for the company")
    target_persona: str = Field(
        ...,
        description="a target user persona for the tool (e.g. Product Manager, Sales, Engineer, CEO, etc.)",
    )
    features: List[str] = Field(..., description="a list of features for the company")
    integrations: List[str] = Field(..., description="a list of integrations for the company")
    investor_vcs: List[str] = Field(..., description="a list of investors by VC name")
    investor_leads: List[str] = Field(..., description="a list of investors by lead investor name")
    relevant_urls: List[str] = Field(..., description="a list of relevant urls for your research")


class ResearchComplete(BaseModel):
    """When you're done with your research, use this function to fill in your answer for competitive research"""

    company_profile: CompanyProfile = Field(..., description="the company profile")
    remaining_tasks: List[str] = Field(..., description="a list of remaining tasks to complete")

    def execute(self):
        return self.model_dump()
