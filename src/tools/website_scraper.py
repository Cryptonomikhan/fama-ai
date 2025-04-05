import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Optional, Dict, Any
from agno.tools import Toolkit
import re
import time
import concurrent.futures
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteScraperTools(Toolkit):
    """Tools for scraping and extracting content from websites"""
    
    def __init__(self, user_agent: str = None, timeout: int = 10, max_workers: int = 5):
        super().__init__(name="website_scraper_tools")
        
        # Set default user agent if not provided
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = timeout
        self.max_workers = max_workers
        
        # Register all the functions
        self.register(self.scrape_url)
        self.register(self.scrape_multiple_urls)
        self.register(self.extract_text_from_html)
        self.register(self.summarize_webpage)
    
    def _get_headers(self) -> Dict[str, str]:
        """Return headers for HTTP requests"""
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def scrape_url(self, url: str, max_length: Optional[int] = None) -> str:
        """
        Scrape content from a given URL
        
        Args:
            url: The URL to scrape
            max_length: Optional maximum length of the returned content
            
        Returns:
            The extracted text content from the URL
        """
        logger.info(f"Scraping URL: {url}")
        
        try:
            # Make the request with a timeout
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                # Extract text content
                html_content = response.text
                text_content = self.extract_text_from_html(html_content)
                
                # Truncate if max_length is specified
                if max_length and len(text_content) > max_length:
                    text_content = text_content[:max_length] + "... [truncated]"
                
                return text_content
            else:
                return f"Error: Failed to fetch the URL. Status code: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return f"Error: Request to {url} timed out after {self.timeout} seconds"
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
    
    def scrape_multiple_urls(self, urls: List[str], max_workers: Optional[int] = None, max_length_per_url: Optional[int] = None) -> str:
        """
        Scrape content from multiple URLs in parallel
        
        Args:
            urls: List of URLs to scrape
            max_workers: Maximum number of parallel workers (default: 5)
            max_length_per_url: Optional maximum length of content per URL
            
        Returns:
            Formatted string containing content from all URLs
        """
        logger.info(f"Scraping {len(urls)} URLs in parallel")
        
        workers = max_workers or self.max_workers
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit scraping tasks
            future_to_url = {
                executor.submit(self.scrape_url, url, max_length_per_url): url
                for url in urls
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    results[url] = f"Error: {str(e)}"
            
            # Format results as a string
            formatted_output = "## Content From Multiple URLs\n\n"
            for url, content in results.items():
                formatted_output += f"### Source: {url}\n\n"
                # Extract a snippet (first 1000 chars)
                snippet = content[:1000] + "..." if len(content) > 1000 else content
                formatted_output += f"{snippet}\n\n---\n\n"
                
            return formatted_output
    
    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract readable text content from HTML
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Extracted text content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
                script_or_style.extract()
            
            # Get text and clean it up
            text = soup.get_text()
            
            # Remove extra whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def summarize_webpage(self, url: str, extract_links: bool = False) -> str:
        """
        Provide a summary of a webpage including title, text content, and optionally links
        
        Args:
            url: URL to summarize
            extract_links: Whether to extract links from the page
            
        Returns:
            String with webpage summary information
        """
        logger.info(f"Summarizing webpage: {url}")
        
        try:
            # Make the request with a timeout
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title = soup.title.string if soup.title else "No title found"
                
                # Extract meta description
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"})
                if meta_tag and "content" in meta_tag.attrs:
                    meta_desc = meta_tag["content"]
                
                # Extract main content
                main_content = self.extract_text_from_html(html_content)
                
                # Format as string
                summary = f"# {title}\n\n"
                
                if meta_desc:
                    summary += f"## Description\n{meta_desc}\n\n"
                
                summary += f"## URL\n{url}\n\n"
                summary += f"## Content\n{main_content[:1000] + '...' if len(main_content) > 1000 else main_content}\n\n"
                
                # Extract links if requested
                if extract_links:
                    summary += "## Links\n"
                    link_count = 0
                    
                    for link in soup.find_all('a', href=True):
                        if link_count >= 20:  # Limit to top 20 links
                            break
                            
                        href = link['href']
                        if href.startswith('http'):
                            full_url = href
                        elif href.startswith('/'):
                            # Convert relative URLs to absolute
                            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
                            full_url = urljoin(base_url, href)
                        else:
                            continue
                            
                        link_text = link.get_text().strip()
                        if link_text and full_url:
                            link_text = link_text if len(link_text) < 100 else link_text[:100] + "..."
                            summary += f"- [{link_text}]({full_url})\n"
                            link_count += 1
                
                return summary
            else:
                return f"Error: Failed to fetch the URL {url}. Status code: {response.status_code}"
                
        except Exception as e:
            return f"Error: Unable to summarize webpage {url}. {str(e)}" 