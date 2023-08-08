from competitive_analysis_gpt.commands import browse


url = "https://www.example.com"
markdown_content = browse.scrape_and_convert_to_markdown(url)
print(markdown_content)
