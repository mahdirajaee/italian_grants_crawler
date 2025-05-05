import logging
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from datetime import datetime

from core.base_crawler import BaseCrawler


class LombardiaCrawler(BaseCrawler):
    """
    Crawler for Regione Lombardia grants.
    """
    
    def __init__(self, max_pages: int = 10, delay: float = 1.0):
        """
        Initialize the Lombardia crawler.
        
        Args:
            max_pages (int): Maximum number of pages to crawl
            delay (float): Delay between requests in seconds
        """
        super().__init__(
            base_url="https://www.bandi.regione.lombardia.it",
            max_pages=max_pages,
            delay=delay
        )
        self.logger = logging.getLogger("LombardiaCrawler")
    
    def get_grant_listing_urls(self) -> List[str]:
        """
        Get URLs for individual grant listings from Regione Lombardia.
        
        Returns:
            List[str]: List of URLs to individual grant pages
        """
        grants_url = "/servizi/servizio/bandi"
        soup = self.get_page(grants_url)
        
        if not soup:
            self.logger.error("Failed to fetch grants list page")
            return []
        
        grant_urls = []
        
        # Find all grant cards in the bandi list
        grant_cards = soup.select(".card.card-bg.card-big")
        
        for card in grant_cards:
            # Look for "Scopri di più" link
            scopri_links = [a for a in card.find_all('a') if 'Scopri' in a.text]
            if scopri_links and scopri_links[0].has_attr("href"):
                grant_url = scopri_links[0]["href"]
                full_url = urljoin(self.base_url, grant_url)
                grant_urls.append(full_url)
        
        # Handle pagination if needed
        pagination = soup.select_one(".pagination")
        if pagination:
            # Find all page links
            page_links = pagination.select("a.page-link:not(.next):not(.prev)")
            
            # Process additional pages (up to max_pages)
            pages_processed = 1
            for page_link in page_links[:min(len(page_links), self.max_pages - 1)]:
                if pages_processed >= self.max_pages:
                    break
                    
                page_url = page_link["href"]
                full_page_url = urljoin(self.base_url, page_url)
                page_soup = self.get_page(full_page_url)
                
                if page_soup:
                    more_grant_urls = self._extract_grant_urls_from_page(page_soup)
                    grant_urls.extend(more_grant_urls)
                    pages_processed += 1
        
        return grant_urls
    
    def _extract_grant_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """
        Helper method to extract grant URLs from a page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML of a page with grant listings
            
        Returns:
            List[str]: List of grant URLs
        """
        urls = []
        
        # Find all grant cards
        grant_cards = soup.select(".card.card-bg.card-big")
        
        for card in grant_cards:
            # Look for "Scopri di più" link
            scopri_links = [a for a in card.find_all('a') if 'Scopri' in a.text]
            if scopri_links and scopri_links[0].has_attr("href"):
                grant_url = scopri_links[0]["href"]
                full_url = urljoin(self.base_url, grant_url)
                urls.append(full_url)
        
        return urls
    
    def parse_grant_details(self, url: str) -> Dict[str, Any]:
        """
        Parse the details of a grant from Regione Lombardia.
        
        Args:
            url (str): URL of the grant detail page
            
        Returns:
            Dict[str, Any]: Grant details in the required format
        """
        soup = self.get_page(url)
        
        if not soup:
            self.logger.error(f"Failed to fetch grant page: {url}")
            return {}
        
        grant_data = {
            "Link Bando": url,
            "Link al sito del bando": url,
            "Emanazione": "Regionale",
            "Località_MR": "Lombardia",
            "Data creazione": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Extract grant title (Nome del bando)
        title_element = soup.select_one("h1")
        if title_element:
            grant_data["Nome del bando"] = title_element.text.strip()
        
        # Extract grant code for reference
        code_element = soup.select_one("span.codice")
        grant_code = None
        if code_element:
            code_text = code_element.text.strip()
            if 'Codice:' in code_text:
                grant_code = code_text.replace('Codice:', '').strip()
        
        # Extract short description (Descrizione breve)
        # First try to find a lead paragraph
        desc_element = soup.select_one(".lead")
        if desc_element:
            grant_data["Descrizione breve (Plain text)"] = desc_element.text.strip()
        
        # Extract full description from the informative section
        info_section = soup.select_one(".scheda-informativa")
        if info_section:
            # Try to find "Di cosa si tratta" section
            di_cosa_heading = None
            for h3 in info_section.select("h3"):
                if "Di cosa si tratta" in h3.text:
                    di_cosa_heading = h3
                    break
            
            if di_cosa_heading:
                # Get the next dd element which contains the description
                desc_dd = di_cosa_heading.find_next("dd")
                if desc_dd:
                    grant_data["Descrizione del bando"] = desc_dd.text.strip()
                    # If we don't have a short description yet, use this as well
                    if "Descrizione breve (Plain text)" not in grant_data:
                        # Truncate for short description
                        short_desc = desc_dd.text.strip()
                        if len(short_desc) > 300:
                            short_desc = short_desc[:297] + "..."
                        grant_data["Descrizione breve (Plain text)"] = short_desc
        
        # If we still don't have a description, use the title as a fallback
        if "Descrizione breve (Plain text)" not in grant_data and "Nome del bando" in grant_data:
            grant_data["Descrizione breve (Plain text)"] = grant_data["Nome del bando"]
        
        if "Descrizione del bando" not in grant_data and "Descrizione breve (Plain text)" in grant_data:
            grant_data["Descrizione del bando"] = grant_data["Descrizione breve (Plain text)"]
        
        # Extract deadlines from the header section
        deadline_element = soup.select_one("span:-soup-contains('Scade il:')")
        if deadline_element and deadline_element.next_sibling:
            deadline_text = deadline_element.next_sibling.strip()
            grant_data["Scadenza"] = deadline_text
            
            # Try to parse the date for internal deadline
            try:
                # Assuming Italian date format (DD/MM/YYYY)
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', deadline_text)
                if date_match:
                    grant_data["Scadenza interna"] = date_match.group(1)
            except:
                self.logger.warning(f"Could not parse deadline date: {deadline_text}")
        
        # Try to extract opening date (Data di apertura)
        opening_date_element = soup.select_one("span:-soup-contains('Domande dal:')")
        if opening_date_element and opening_date_element.next_sibling:
            opening_date_text = opening_date_element.next_sibling.strip()
            grant_data["Data di apertura"] = opening_date_text
        
        # Extract additional information from the "Scheda informativa" section
        if info_section:
            sections = info_section.select("h3")
            
            for section in sections:
                section_title = section.text.strip()
                next_dd = section.find_next("dd")
                
                if next_dd:
                    text = next_dd.text.strip()
                    
                    if section_title == "Chi può partecipare":
                        grant_data["A chi si rivolge"] = text
                    elif section_title == "Come partecipare":
                        grant_data["Iter presentazione della domanda"] = text
                    elif section_title == "Procedura di selezione":
                        grant_data["Tipo"] = text
        
        # Extract attachments (if any)
        attachments_section = soup.select_one(".allegati")
        if attachments_section:
            attachments = self._extract_attachments(attachments_section)
            if attachments:
                if attachments.get("compilativi"):
                    grant_data["Allegato Compilativo - X"] = ", ".join(attachments["compilativi"])
                if attachments.get("informativi"):
                    grant_data["Allegato informativo - X"] = ", ".join(attachments["informativi"])
        
        return grant_data
    
    def _extract_attachments(self, attachments_section: BeautifulSoup) -> Dict[str, List[str]]:
        """
        Extract attachment links from the grant page.
        
        Args:
            attachments_section (BeautifulSoup): Parsed HTML of the attachments section
            
        Returns:
            Dict[str, List[str]]: Dictionary with attachment types and links
        """
        attachments = {
            "compilativi": [],
            "informativi": []
        }
        
        # Find all attachment links
        links = attachments_section.select("a")
        
        for link in links:
            # Assume all attachments are informative by default
            attachment_type = "informativi"
            
            # Check if the link or parent element contains text that indicates it's a form to fill
            link_text = link.text.lower()
            if any(keyword in link_text for keyword in ["modulo", "modell", "compil", "domanda", "modell", "richiesta"]):
                attachment_type = "compilativi"
            
            if link.has_attr("href"):
                url = link["href"]
                if url.startswith(('http://', 'https://')):
                    attachments[attachment_type].append(url)
                else:
                    full_url = urljoin(self.base_url, url)
                    attachments[attachment_type].append(full_url)
        
        return attachments