import logging
import re
from typing import List, Dict, Any, Optional, Tuple
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
        
        # Extract document requirements using improved document detection
        full_text = self._get_full_grant_text(soup)
        doc_requirements, doc_contexts = self._extract_document_requirements(full_text)
        if doc_requirements:
            grant_data["Documentazione necessaria"] = "\n".join(f"- {doc}" for doc in doc_requirements)
        
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
    
    def _get_full_grant_text(self, soup: BeautifulSoup) -> str:
        """
        Extract all relevant text from the grant page for document detection.
        
        Args:
            soup (BeautifulSoup): Parsed HTML of the grant page
            
        Returns:
            str: Concatenated text from relevant sections
        """
        text_parts = []
        
        # Get title
        title = soup.select_one("h1")
        if title:
            text_parts.append(title.text.strip())
        
        # Get description
        desc = soup.select_one(".lead")
        if desc:
            text_parts.append(desc.text.strip())
        
        # Get all content from informative section
        info_section = soup.select_one(".scheda-informativa")
        if info_section:
            for dd in info_section.select("dd"):
                text_parts.append(dd.text.strip())
        
        # Get all content from attachment section
        attachments = soup.select_one(".allegati")
        if attachments:
            text_parts.append(attachments.text.strip())
        
        return "\n\n".join(text_parts)
    
    def _extract_document_requirements(self, text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Extract document requirements from text using improved detection.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Tuple[List[str], Dict[str, List[str]]]: List of required documents and their contexts
        """
        target_words = self._get_document_target_words()
        return self.find_target_words(text, target_words)
    
    def _get_document_target_words(self) -> List[str]:
        """Return list of target words to search for in documents."""
        # Common document types required for Italian grants
        return [
            "carta d'identità", "documento identità", "copia carta identità", 
            "codice fiscale", "CF", "documento soci", "documenti anagrafici",
            "attribuzione codice fiscale", "certificato codice fiscale",
            "certificato partita IVA", "attribuzione P.IVA", "partita IVA",
            "registro imprese", "iscrizione CCIAA", "certificato camera commercio", 
            "visura CCIAA", "visura camerale", "visura ordinaria", 
            "visura immobile", "visura catastale", "documento catastale",
            "atto costitutivo", "statuto società", "atti sociali", 
            "atto nomina rappresentante", "nomina amministratore", 
            "delega firma", "delega sottoscrizione", "delega rappresentanza",
            "DSAN", "dichiarazione sostitutiva", "autocertificazione", 
            "dichiarazione d'intenti", "manifestazione di interesse",
            "certificato casellario", "casellario penale", "assenza condanne penali",
            "DURC", "documento regolarità contributiva", "regolarità contributiva",
            "certificato fiscale", "regolarità fiscale", "assenza carichi pendenti",
            "dichiarazione antiriciclaggio", "dichiarazione antimafia", 
            "contributo ANAC", "pagamento ANAC", "ricevuta ANAC",
            "piano finanziario", "budget", "preventivo economico", 
            "bilancio", "stato patrimoniale", "situazione economico-patrimoniale",
            "dichiarazione redditi", "modello Redditi", "730", 
            "dichiarazioni IVA", "IVA annuale", "modello IVA",
            "fideiussione bancaria", "fideiussione assicurativa", "garanzia fideiussoria",
            "ricevute pagamento", "prova pagamento", "quietanze pagamento",
            "fatture", "fatture elettroniche", "fatture PA", "e-fatture",
            "giustificativi di spesa", "documenti di spesa", "pezze giustificative",
            "scheda progetto", "sintesi progetto", "scheda descrittiva",
            "programma operativo", "cronoprogramma", "piano attività",
            "diagramma di Gantt", "gantt chart", "timeline progetto",
            "relazione finale", "report finale", "rendicontazione finale",
            "relazione lavori", "relazione attività", "stato avanzamento lavori",
            "PSC", "piano sicurezza", "documento coordinamento sicurezza",
            "dichiarazione localizzazione", "ubicazione intervento", 
            "assenso proprietario", "dichiarazione consenso", "nulla osta proprietà",
            "contratto affitto", "contratto locazione", "contratto comodato",
            "progetto impresa", "business plan", "piano d'impresa", 
            "pitch", "presentazione sintetica", "elevator pitch", "pitch deck",
            "CV team", "curriculum", "profilo fondatori", 
            "attestato corso", "attestato formazione", "certificato partecipazione",
            "certificazione qualità", "certificato ISO", 
            "certificato conformità", "conformità impianto", "conformità normativa",
            "attestazione SOA", "certificazione SOA", "qualificazione per appalti pubblici",
            "brevetto", "certificato di brevetto", "titolo brevettuale",
            "IBAN", "certificato IBAN", "coordinate bancarie"
        ]
        
    def find_target_words(self, text: str, target_words: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Find target words and phrases in text using advanced context verification.
        
        Args:
            text (str): Text to analyze
            target_words (List[str]): List of target words to search for
            
        Returns:
            Tuple[List[str], Dict[str, List[str]]]: List of found words and their contexts
        """
        found_words = []
        context_dict = {}
        
        if not text or not text.strip():
            return found_words, context_dict
        
        # Normalize text
        text = text.lower()
        
        # Define validation keywords that would indicate a document is required
        validation_keywords = [
            "allegare", "allegato", "presentare", "presentazione", "fornire", 
            "obbligatorio", "necessario", "richiesto", "documentazione", 
            "consegnare", "produrre", "trasmettere", "accompagnato da", 
            "corredato da", "da presentare", "dovranno essere allegati", 
            "è richiesto", "è necessario", "deve essere allegato", 
            "va allegato", "documenti da allegare", "è obbligatorio", 
            "completo di", "comprensivo di", "deve riportare", 
            "da compilare", "da firmare", "firmato", "sottoscritto", 
            "va presentato", "si richiede", "sarà necessario", 
            "documento richiesto", "da trasmettere", "occorre presentare", 
            "documento obbligatorio", "insieme a", "copia", "file", "modulo"
        ]
        
        # Define common false positive contexts to exclude
        exclusion_contexts = [
            "non è necessario", "non è richiesto", "non obbligatorio", 
            "facoltativo", "non è obbligatorio", "non deve essere allegato", 
            "non sarà richiesto", "non sono richiesti", "opzionale"
        ]
        
        # High-priority documents that are almost always required if mentioned
        critical_documents = [
            "codice fiscale", "carta d'identità", "documento identità", 
            "partita iva", "visura camerale", "durc", "iban", "preventivi"
        ]
        
        for target in target_words:
            target_lower = target.lower()
            
            # Increase the context window for critical documents
            context_window = 300 if target_lower in critical_documents else 200
            
            # Only proceed if the target word is actually present in the text
            if target_lower in text:
                # For multi-word phrases, use regex with word boundaries
                if ' ' in target_lower or len(target_lower) > 3:  # Ignore very short single words
                    # Create pattern with word boundaries that's case insensitive
                    escaped_target = re.escape(target_lower)
                    pattern = r'(?i)\b' + escaped_target + r'\b'
                    
                    try:
                        matches = list(re.finditer(pattern, text))
                        
                        if matches:
                            # Analyze context to confirm it's actually required
                            valid_match = False
                            contexts = []
                            
                            for match in matches:
                                # Extract a context window
                                start = max(0, match.start() - context_window)
                                end = min(len(text), match.end() + context_window)
                                context = text[start:end]
                                
                                # Skip if in exclusion context
                                if any(excl in context for excl in exclusion_contexts):
                                    continue
                                
                                # For critical documents, we have relaxed validation requirements
                                if target_lower in critical_documents:
                                    if any(kw in context for kw in validation_keywords):
                                        valid_match = True
                                        # Highlight the match in the context
                                        matched_text = text[match.start():match.end()]
                                        highlighted = f"...{text[start:match.start()]}**{matched_text}**{text[match.end():end]}..."
                                        contexts.append(highlighted)
                                else:
                                    # For non-critical documents, require stricter validation
                                    found_keywords = [kw for kw in validation_keywords if kw in context]
                                    if found_keywords:
                                        valid_match = True
                                        # Highlight the match in the context
                                        matched_text = text[match.start():match.end()]
                                        highlighted = f"...{text[start:match.start()]}**{matched_text}**{text[match.end():end]}..."
                                        contexts.append(highlighted)
                            
                            if valid_match:
                                found_words.append(target)
                                context_dict[target] = contexts
                    except re.error:
                        self.logger.warning(f"Regex error for pattern '{target_lower}'")
        
        return found_words, context_dict