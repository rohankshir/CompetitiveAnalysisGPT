from . import browse


def search_and_get_crunchbase_financials(company_name: str, keywords: str = None):
    search_terms = company_name + " crunchbase"
    if keywords:
        search_terms += " " + keywords
    results = browse.search_urls_and_preview(search_terms, 3)
    url = None
    for result in results:
        if "crunchbase.com" in result["href"]:
            url = result["href"]
            break

    url += "/company_financials"
    result = browse.scrape_and_convert_to_markdown(url)

    # Trim out the first part of the markdown and last part, start at \nOrganization\n and end at "Unlock even more features"
    # TODO: This is brittle, find a better way to do this

    result = result.split("\nOrganization\n")[1]
    result = result.split("Unlock even more features")[0]
    return result


def get_crunchbase_financials(url: str):
    url += "/company_financials"
    result = browse.scrape_and_convert_to_markdown(url)

    # Trim out the first part of the markdown and last part, start at \nOrganization\n and end at "Unlock even more features"
    # TODO: This is brittle, find a better way to do this

    result = result.split("\nOrganization\n")[1]
    result = result.split("Unlock even more features")[0]
    return result


def get_crunchbase_financials_for_companies(company_names, keywords=None):
    results = []
    for company_name in company_names:
        result = get_crunchbase_financials(company_name, keywords)
        results.append(result)
    return results


def resolve_company_urls(company_names):
    pass
