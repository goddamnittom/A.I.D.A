"""
Simple web search / browse tools.
For more advanced scraping, add playwright or use external services.
"""

import requests
from bs4 import BeautifulSoup
from .base import run_command

def web_search(args: dict, config: dict = None) -> str:
    """Basic web search using DuckDuckGo HTML (no API key)."""
    query = args.get("query", "")
    if not query:
        return "Error: No query provided"
    
    try:
        # Simple DuckDuckGo scrape
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TermuxAgent/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        
        results = []
        for result in soup.select(".result__a")[:5]:
            title = result.get_text(strip=True)
            link = result.get("href", "")
            results.append(f"• {title} - {link}")
        
        return "\n".join(results) if results else "No results found."
        
    except Exception as e:
        return f"Search error: {str(e)}"

def browse_page(args: dict, config: dict = None) -> str:
    """Fetch and summarize a page (basic version)."""
    url = args.get("url", "")
    if not url:
        return "Error: No URL"
    
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "TermuxAgent/1.0"})
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Get main text
        text = soup.get_text(separator=" ", strip=True)[:2000]
        return f"Page summary (first 2000 chars):\n{text}"
    except Exception as e:
        return f"Browse error: {str(e)}"