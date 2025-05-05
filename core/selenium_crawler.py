import logging
import time
import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

import config
from core.base_crawler import BaseCrawler


class SeleniumCrawler(BaseCrawler, ABC):
    """
    Selenium-based crawler for JavaScript-heavy websites.
    Inherits from BaseCrawler and extends its functionality.
    """
    
    def __init__(self, base_url: str, max_pages: int = 10, delay: float = 1.0, timeout: int = 30):
        """
        Initialize the Selenium crawler.
        
        Args:
            base_url (str): The base URL of the website to crawl
            max_pages (int): Maximum number of pages to crawl
            delay (float): Delay between requests in seconds
            timeout (int): Request timeout in seconds
        """
        super().__init__(base_url, max_pages, delay, timeout)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.driver = None
        self.initialize_driver()
    
    def initialize_driver(self):
        """Initialize the Selenium WebDriver."""
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Set a random user agent
            user_agent = random.choice(config.USER_AGENTS)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Initialize the WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            
            self.logger.info("Selenium WebDriver initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            # Re-raise the exception to allow the caller to handle it
            raise
    
    def __del__(self):
        """Clean up resources on object destruction."""
        self.close_driver()
    
    def close_driver(self):
        """Close the WebDriver if it exists."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Selenium WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing Selenium WebDriver: {e}")
    
    def get_page_with_selenium(self, url: str, wait_for_selector: Optional[str] = None, wait_time: int = 10) -> BeautifulSoup:
        """
        Fetch a page using Selenium and return its BeautifulSoup object.
        
        Args:
            url (str): URL to fetch
            wait_for_selector (str, optional): CSS selector to wait for before parsing
            wait_time (int): Maximum time to wait for selector in seconds
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
            
        self.logger.info(f"Fetching page with Selenium: {url}")
        
        try:
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for specific element if requested
            if wait_for_selector:
                try:
                    WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                except TimeoutException:
                    self.logger.warning(f"Timeout waiting for selector '{wait_for_selector}' on {url}")
            
            # Additional delay to ensure JS execution
            time.sleep(self.delay)
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except WebDriverException as e:
            self.logger.error(f"Selenium error fetching {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {url} with Selenium: {e}")
            return None
    
    def click_element_and_get_content(self, selector: str, wait_time: int = 10) -> BeautifulSoup:
        """
        Click on an element and return the resulting page content.
        
        Args:
            selector (str): CSS selector of the element to click
            wait_time (int): Maximum time to wait after clicking
            
        Returns:
            BeautifulSoup: Parsed HTML after click
        """
        try:
            # Find and click the element
            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            
            # Wait for the page to load
            time.sleep(self.delay)
            
            # Get updated page source
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            self.logger.error(f"Error clicking element '{selector}': {e}")
            return None
    
    def scroll_to_bottom(self, scroll_pause_time: float = 1.0, max_scrolls: int = 10) -> BeautifulSoup:
        """
        Scroll to the bottom of the page to load lazy-loaded content.
        
        Args:
            scroll_pause_time (float): Time to pause between scrolls
            max_scrolls (int): Maximum number of scroll operations
            
        Returns:
            BeautifulSoup: Parsed HTML after scrolling
        """
        try:
            # Get initial scroll height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for _ in range(max_scrolls):
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for page to load
                time.sleep(scroll_pause_time)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # If heights are the same, we've reached the bottom
                    break
                    
                last_height = new_height
            
            # Get final page source
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            self.logger.error(f"Error scrolling page: {e}")
            return None
    
    def fill_form_and_submit(self, form_data: Dict[str, str], submit_selector: str) -> BeautifulSoup:
        """
        Fill in a form and submit it.
        
        Args:
            form_data (Dict[str, str]): Map of field selectors to values
            submit_selector (str): CSS selector for the submit button
            
        Returns:
            BeautifulSoup: Parsed HTML after form submission
        """
        try:
            # Fill in form fields
            for selector, value in form_data.items():
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.clear()
                element.send_keys(value)
                time.sleep(0.5)  # Small delay between fields
            
            # Submit the form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, submit_selector)
            submit_button.click()
            
            # Wait for the page to load
            time.sleep(self.delay * 2)  # Double delay after form submission
            
            # Get updated page source
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return None