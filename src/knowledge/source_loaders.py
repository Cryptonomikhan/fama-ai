#!/usr/bin/env python3
"""
Knowledge source loaders for Fama AI.

This module provides loaders for different types of knowledge sources,
including URL-based sources (PDF, HTML, etc.) and text-based sources.
"""
import os
import logging
import time
import tempfile
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any, Tuple, Union
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class KnowledgeSourceLoadError(Exception):
    """Exception raised when a knowledge source cannot be loaded."""
    pass

class URLLoader:
    """Base class for URL-based knowledge source loaders."""
    
    def __init__(
        self,
        urls: List[str],
        load_concurrent: int = 3,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
        user_agent: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Initialize the URL loader.
        
        Args:
            urls: List of URLs to load
            load_concurrent: Number of URLs to load concurrently
            timeout: Timeout for URL requests in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            user_agent: User agent to use for requests
            **kwargs: Additional keyword arguments
        """
        self.urls = urls
        self.load_concurrent = load_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.temp_dir = tempfile.mkdtemp(prefix="fama_kb_")
        
        # Downloaded content cache
        self.content_cache = {}
        
        # Results
        self.successful_urls = []
        self.failed_urls = []
        
        # Parse additional kwargs
        self.kwargs = kwargs
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get headers for HTTP requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def validate_url(self, url: str) -> bool:
        """
        Validate a URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if the URL is valid, False otherwise
        """
        try:
            parsed_url = urllib.parse.urlparse(url)
            return all([parsed_url.scheme, parsed_url.netloc])
        except Exception:
            return False
    
    def download_url(self, url: str) -> Optional[bytes]:
        """
        Download content from a URL with retries.
        
        Args:
            url: URL to download
            
        Returns:
            Content as bytes if successful, None otherwise
        """
        if url in self.content_cache:
            logger.info(f"Using cached content for {url}")
            return self.content_cache[url]
        
        headers = self.get_headers()
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Downloading {url} (attempt {attempt + 1}/{self.max_retries})")
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                if response.status_code >= 400:
                    logger.warning(f"HTTP error {response.status_code} for {url}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                
                content = response.content
                self.content_cache[url] = content
                return content
            except requests.RequestException as e:
                logger.warning(f"Error downloading {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None
        
        return None
    
    def save_to_temp_file(self, url: str, content: bytes) -> Optional[str]:
        """
        Save content to a temporary file.
        
        Args:
            url: Original URL (used for filename)
            content: Content to save
            
        Returns:
            Path to the temporary file if successful, None otherwise
        """
        try:
            # Create a filename based on the URL
            parsed_url = urllib.parse.urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            filename = path_parts[-1] if path_parts else "unnamed"
            
            # Remove query parameters and ensure there's a proper extension
            filename = filename.split('?')[0]
            
            if not filename or '.' not in filename:
                # If no filename or no extension, generate a name based on URL host
                filename = f"{parsed_url.netloc.replace('.', '_')}_{int(time.time())}.bin"
            
            # Create the file path
            file_path = os.path.join(self.temp_dir, filename)
            
            # Save the content
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved content from {url} to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving content from {url}: {str(e)}")
            return None
    
    def process_url(self, url: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a single URL.
        
        This method should be implemented by subclasses to handle specific URL types.
        
        Args:
            url: URL to process
            
        Returns:
            Tuple of (success, result_data)
        """
        raise NotImplementedError("Subclasses must implement process_url")
    
    def load_urls(self) -> Dict[str, Any]:
        """
        Load all URLs concurrently.
        
        Returns:
            Dictionary with loading results
        """
        start_time = time.time()
        logger.info(f"Loading {len(self.urls)} URLs with concurrency {self.load_concurrent}")
        
        # Validate URLs first
        valid_urls = []
        for url in self.urls:
            if self.validate_url(url):
                valid_urls.append(url)
            else:
                logger.warning(f"Invalid URL: {url}")
                self.failed_urls.append((url, "Invalid URL format"))
        
        # Process the valid URLs concurrently
        with ThreadPoolExecutor(max_workers=self.load_concurrent) as executor:
            results = list(executor.map(self.process_url, valid_urls))
        
        # Process results
        for i, (success, result_data) in enumerate(results):
            url = valid_urls[i]
            if success:
                self.successful_urls.append(url)
            else:
                self.failed_urls.append((url, result_data.get("error", "Unknown error")))
        
        elapsed_time = time.time() - start_time
        
        # Build result summary
        result = {
            "total_urls": len(self.urls),
            "successful_urls": len(self.successful_urls),
            "failed_urls": len(self.failed_urls),
            "elapsed_time": elapsed_time,
            "failures": self.failed_urls
        }
        
        logger.info(f"URL loading completed in {elapsed_time:.2f}s - Success: {result['successful_urls']}, Failed: {result['failed_urls']}")
        return result
    
    def cleanup(self) -> None:
        """
        Clean up temporary resources.
        """
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning up temporary directory: {str(e)}")


class PDFURLLoader(URLLoader):
    """
    Loader for PDF URLs.
    
    This loader downloads PDFs from URLs and processes them for the knowledge base.
    """
    
    def __init__(
        self,
        urls: List[str],
        extractor_type: str = "default",
        extract_images: bool = False,
        **kwargs: Any
    ):
        """
        Initialize the PDF URL loader.
        
        Args:
            urls: List of PDF URLs to load
            extractor_type: Type of PDF extractor to use (default, pymupdf, etc.)
            extract_images: Whether to extract images from PDFs
            **kwargs: Additional keyword arguments passed to the URLLoader
        """
        super().__init__(urls, **kwargs)
        self.extractor_type = extractor_type
        self.extract_images = extract_images
        self.pdf_files = []
        self.extracted_text = {}
    
    def is_pdf_url(self, url: str) -> bool:
        """
        Check if a URL points to a PDF document.
        
        Args:
            url: URL to check
            
        Returns:
            True if the URL likely points to a PDF, False otherwise
        """
        # Check URL extension
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        
        # Direct check for .pdf extension
        if path.endswith('.pdf'):
            return True
        
        # If the URL doesn't have a clear extension, we'll need to make a HEAD request
        # to check the content type
        try:
            headers = self.get_headers()
            response = requests.head(url, headers=headers, timeout=self.timeout)
            content_type = response.headers.get('Content-Type', '').lower()
            
            return 'application/pdf' in content_type
        except requests.RequestException:
            # If the HEAD request fails, we'll assume it's not a PDF
            return False
    
    def process_url(self, url: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a single PDF URL.
        
        Args:
            url: PDF URL to process
            
        Returns:
            Tuple of (success, result_data)
        """
        logger.info(f"Processing PDF URL: {url}")
        result_data = {"url": url, "type": "pdf"}
        
        # Check if it's a PDF URL
        if not self.is_pdf_url(url):
            logger.warning(f"URL does not appear to be a PDF: {url}")
            result_data["error"] = "URL does not appear to be a PDF"
            return False, result_data
        
        # Download the PDF
        content = self.download_url(url)
        if content is None:
            logger.error(f"Failed to download PDF from {url}")
            result_data["error"] = "Failed to download PDF"
            return False, result_data
        
        # Save to temporary file
        file_path = self.save_to_temp_file(url, content)
        if file_path is None:
            logger.error(f"Failed to save PDF from {url}")
            result_data["error"] = "Failed to save PDF"
            return False, result_data
        
        # Store the file path for later processing
        self.pdf_files.append((url, file_path))
        result_data["file_path"] = file_path
        
        # At this point, we've successfully downloaded and saved the PDF
        # The actual parsing will be handled separately in a dedicated method
        return True, result_data
    
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text if successful, None otherwise
        """
        try:
            # We'll try to import PyMuPDF for PDF text extraction
            import fitz  # PyMuPDF

            logger.info(f"Extracting text from PDF: {file_path}")
            text_parts = []
            
            try:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    text_parts.append(text)
                
                doc.close()
                
                extracted_text = "\n\n".join(text_parts)
                logger.info(f"Successfully extracted {len(text_parts)} pages from {file_path}")
                return extracted_text
            except Exception as e:
                logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
                return None
        except ImportError:
            logger.error("PyMuPDF (fitz) is not installed. Please install it with 'pip install pymupdf'")
            return None
    
    def extract_all_text(self) -> Dict[str, str]:
        """
        Extract text from all downloaded PDFs.
        
        Returns:
            Dictionary mapping URLs to extracted text
        """
        logger.info(f"Extracting text from {len(self.pdf_files)} PDF files")
        
        with ThreadPoolExecutor(max_workers=self.load_concurrent) as executor:
            for url, file_path in self.pdf_files:
                # Submit each PDF file for text extraction
                future = executor.submit(self.extract_text_from_pdf, file_path)
                try:
                    extracted_text = future.result()
                    if extracted_text:
                        self.extracted_text[url] = extracted_text
                    else:
                        logger.warning(f"No text extracted from {url}")
                except Exception as e:
                    logger.error(f"Error processing extraction for {url}: {str(e)}")
        
        logger.info(f"Successfully extracted text from {len(self.extracted_text)} out of {len(self.pdf_files)} PDF files")
        return self.extracted_text
    
    def load(self) -> Dict[str, Any]:
        """
        Load and process PDF URLs.
        
        Returns:
            Dictionary with loading results including extracted text
        """
        # First, download all PDFs
        download_results = self.load_urls()
        
        # Then extract text from the downloaded PDFs
        self.extract_all_text()
        
        # Add extraction results to the overall results
        download_results["extracted_text_count"] = len(self.extracted_text)
        download_results["extracted_text"] = self.extracted_text
        
        return download_results


class WebpageURLLoader(URLLoader):
    """
    Loader for webpage URLs.
    
    This loader downloads HTML content from URLs, extracts the text, and processes it for the knowledge base.
    """
    
    def __init__(
        self,
        urls: List[str],
        extract_all_text: bool = True,
        clean_html: bool = True,
        follow_links: bool = False,
        max_links_per_page: int = 10,
        max_link_depth: int = 1,
        **kwargs: Any
    ):
        """
        Initialize the webpage URL loader.
        
        Args:
            urls: List of webpage URLs to load
            extract_all_text: Whether to extract all text from the webpage (vs. just the main content)
            clean_html: Whether to clean HTML (remove scripts, styles, etc.)
            follow_links: Whether to follow links on the webpage
            max_links_per_page: Maximum number of links to follow per page
            max_link_depth: Maximum depth of links to follow
            **kwargs: Additional keyword arguments passed to the URLLoader
        """
        super().__init__(urls, **kwargs)
        self.extract_all_text = extract_all_text
        self.clean_html = clean_html
        self.follow_links = follow_links
        self.max_links_per_page = max_links_per_page
        self.max_link_depth = max_link_depth
        self.html_content = {}
        self.extracted_text = {}
    
    def process_url(self, url: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a single webpage URL.
        
        Args:
            url: Webpage URL to process
            
        Returns:
            Tuple of (success, result_data)
        """
        logger.info(f"Processing webpage URL: {url}")
        result_data = {"url": url, "type": "webpage"}
        
        # Download the webpage content
        content = self.download_url(url)
        if content is None:
            logger.error(f"Failed to download webpage from {url}")
            result_data["error"] = "Failed to download webpage"
            return False, result_data
        
        # Store the HTML content
        self.html_content[url] = content
        
        # Extract text immediately
        try:
            extracted_text = self.extract_text_from_html(content)
            if extracted_text:
                self.extracted_text[url] = extracted_text
                result_data["text_length"] = len(extracted_text)
                logger.info(f"Extracted {len(extracted_text)} characters from {url}")
            else:
                logger.warning(f"No text extracted from {url}")
                result_data["error"] = "No text extracted"
                return False, result_data
        except Exception as e:
            logger.error(f"Error extracting text from {url}: {str(e)}")
            result_data["error"] = f"Text extraction error: {str(e)}"
            return False, result_data
        
        return True, result_data
    
    def extract_text_from_html(self, html_content: bytes) -> Optional[str]:
        """
        Extract text from HTML content.
        
        Args:
            html_content: HTML content as bytes
            
        Returns:
            Extracted text if successful, None otherwise
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # If clean_html is True, remove script, style, and other non-content elements
            if self.clean_html:
                for element in soup(["script", "style", "meta", "noscript", "iframe", "object"]):
                    element.decompose()
            
            # Extract text from the HTML
            if self.extract_all_text:
                # Extract all text from the document
                text = soup.get_text(separator="\n", strip=True)
            else:
                # Attempt to extract main content only (this is more heuristic)
                main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=["content", "main", "article", "post"])
                if main_content:
                    text = main_content.get_text(separator="\n", strip=True)
                else:
                    # Fall back to all text if no main content is identified
                    text = soup.get_text(separator="\n", strip=True)
            
            # Clean up the text
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = "\n".join(lines)
            
            return cleaned_text if cleaned_text else None
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
            return None
    
    def load(self) -> Dict[str, Any]:
        """
        Load and process webpage URLs.
        
        Returns:
            Dictionary with loading results including extracted text
        """
        # Download all webpages and extract their text
        load_results = self.load_urls()
        
        # Add extraction results to the overall results
        load_results["extracted_text_count"] = len(self.extracted_text)
        load_results["extracted_text"] = self.extracted_text
        
        return load_results


class URLKnowledgeSourceLoader:
    """
    Knowledge source loader for URLs.
    
    This class provides a unified interface for loading knowledge from various URL types.
    """
    
    def __init__(
        self,
        urls: List[str],
        load_concurrent: int = 3,
        auto_detect_type: bool = True,
        **kwargs: Any
    ):
        """
        Initialize the URL knowledge source loader.
        
        Args:
            urls: List of URLs to load
            load_concurrent: Number of URLs to load concurrently
            auto_detect_type: Whether to automatically detect URL types
            **kwargs: Additional keyword arguments passed to specific loaders
        """
        self.urls = urls
        self.load_concurrent = load_concurrent
        self.auto_detect_type = auto_detect_type
        self.kwargs = kwargs
        
        # Group URLs by type
        self.pdf_urls = []
        self.webpage_urls = []
        self.other_urls = []
        
        # Results
        self.loaded_content = {}
        self.failed_urls = []
    
    def detect_url_type(self, url: str) -> str:
        """
        Detect the type of a URL.
        
        Args:
            url: URL to detect type for
            
        Returns:
            URL type ("pdf", "webpage", or "unknown")
        """
        # Check for PDF URLs
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path.lower()
        
        if path.endswith('.pdf'):
            return "pdf"
        
        # For other URLs, assume they're webpages
        return "webpage"
    
    def group_urls_by_type(self) -> None:
        """
        Group URLs by their type.
        """
        for url in self.urls:
            if not self.auto_detect_type:
                # If not auto-detecting, treat all as webpages for now
                self.webpage_urls.append(url)
                continue
            
            url_type = self.detect_url_type(url)
            if url_type == "pdf":
                self.pdf_urls.append(url)
            elif url_type == "webpage":
                self.webpage_urls.append(url)
            else:
                self.other_urls.append(url)
        
        logger.info(f"Grouped URLs by type: {len(self.pdf_urls)} PDFs, {len(self.webpage_urls)} webpages, {len(self.other_urls)} other")
    
    def load(self) -> Dict[str, Any]:
        """
        Load content from all URLs.
        
        Returns:
            Dictionary with loading results including extracted content
        """
        start_time = time.time()
        
        # Group URLs by type
        self.group_urls_by_type()
        
        # Load PDF URLs
        pdf_results = {}
        if self.pdf_urls:
            logger.info(f"Loading {len(self.pdf_urls)} PDF URLs")
            pdf_loader = PDFURLLoader(
                urls=self.pdf_urls,
                load_concurrent=self.load_concurrent,
                **self.kwargs
            )
            pdf_results = pdf_loader.load()
            
            # Add extracted text to the loaded content
            if "extracted_text" in pdf_results:
                self.loaded_content.update(pdf_results["extracted_text"])
            
            # Add failed URLs
            if "failures" in pdf_results:
                self.failed_urls.extend(pdf_results["failures"])
        
        # Load webpage URLs
        webpage_results = {}
        if self.webpage_urls:
            logger.info(f"Loading {len(self.webpage_urls)} webpage URLs")
            webpage_loader = WebpageURLLoader(
                urls=self.webpage_urls,
                load_concurrent=self.load_concurrent,
                **self.kwargs
            )
            webpage_results = webpage_loader.load()
            
            # Add extracted text to the loaded content
            if "extracted_text" in webpage_results:
                self.loaded_content.update(webpage_results["extracted_text"])
            
            # Add failed URLs
            if "failures" in webpage_results:
                self.failed_urls.extend(webpage_results["failures"])
        
        elapsed_time = time.time() - start_time
        
        # Build combined results
        results = {
            "total_urls": len(self.urls),
            "successful_urls": len(self.loaded_content),
            "failed_urls": len(self.failed_urls),
            "elapsed_time": elapsed_time,
            "failures": self.failed_urls,
            "content": self.loaded_content
        }
        
        logger.info(f"URL loading completed in {elapsed_time:.2f}s - Success: {results['successful_urls']}, Failed: {results['failed_urls']}")
        return results 