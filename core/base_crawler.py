import logging
import time
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BaseCrawler(ABC):
    """
    Base crawler class providing common functionality for all website crawlers.
    """
    
    def __init__(self, base_url: str, max_pages: int = 10, delay: float = 1.0, timeout: int = 30):
        """
        Initialize the base crawler.
        
        Args:
            base_url (str): The base URL of the website to crawl
            max_pages (int): Maximum number of pages to crawl
            delay (float): Delay between requests in seconds
            timeout (int): Request timeout in seconds
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=2
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # Create session with retry strategy
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
    
    def get_page(self, url: str, params: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
        """
        Fetch a page and return its BeautifulSoup object.
        
        Args:
            url (str): URL to fetch
            params (dict, optional): Query parameters
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
            
        self.logger.info(f"Fetching page: {url}")
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Respect robots.txt and rate limit
            time.sleep(self.delay)
            
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching page {url}: {e}")
            return None
    
    @abstractmethod
    def get_grant_listing_urls(self) -> List[str]:
        """
        Get URLs for individual grant listings.
        
        Returns:
            List[str]: List of URLs to individual grant pages
        """
        pass
    
    @abstractmethod
    def parse_grant_details(self, url: str) -> Dict[str, Any]:
        """
        Parse the details of a grant from its page.
        
        Args:
            url (str): URL of the grant detail page
            
        Returns:
            Dict[str, Any]: Grant details in the required format
        """
        pass
    
    def crawl(self) -> List[Dict[str, Any]]:
        """
        Crawl the website and collect grant data.
        
        Returns:
            List[Dict[str, Any]]: List of grant details
        """
        self.logger.info(f"Starting to crawl {self.base_url}")
        
        grant_urls = self.get_grant_listing_urls()
        self.logger.info(f"Found {len(grant_urls)} grant listings")
        
        grants = []
        for url in grant_urls[:self.max_pages]:
            try:
                grant_data = self.parse_grant_details(url)
                if grant_data:
                    grants.append(grant_data)
            except Exception as e:
                self.logger.error(f"Error parsing grant details from {url}: {e}")
                continue
        
        self.logger.info(f"Successfully crawled {len(grants)} grants")
        return grants