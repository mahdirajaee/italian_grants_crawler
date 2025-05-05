import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from datetime import datetime

from core.base_crawler import BaseCrawler


class MoliseCrawler(BaseCrawler):
    """
    Crawler for Regione Molise grants (via Molise in Europa portal).
    """
    
    def __init__(self, max_pages: int = 10, delay: float = 1.0):
        """
        Initialize the Molise crawler.
        
        Args:
            max_pages (int): Maximum number of pages to crawl
            delay (float): Delay between requests in seconds
        """
        super().__init__(
            base_url="https://moliseineuropa.regione.molise.it",
            max_pages=max_pages,
            delay=delay
        )
        self.logger = logging.getLogger("MoliseCrawler")
    
    def get_grant_listing_urls(self) -> List[str]:
        """
        Get URLs for individual grant listings from Regione Molise.
        
        Returns:
            List[str]: List of URLs to individual grant pages
        """
        # Molise uses a dedicated EU funds portal
        grants_url = "/bandi"  # Adjust based on actual site structure
        soup = self.get_page(grants_url)
        
        if not soup:
            self.logger.error("Failed to fetch grants list page")
            return []
        
        grant_urls = []
        
        # Find grant links - adjust selector based on site structure
        grant_items = soup.select(".bando-item")  # Adjust based on actual site structure
        
        for item in grant_items:
            link = item.select_one("a.bando-link")  # Adjust selector
            if link and link.has_attr("href"):
                grant_url = link["href"]
                full_url = urljoin(self.base_url, grant_url)
                grant_urls.append(full_url)
        
        # Handle pagination if present
        pagination = soup.select_one(".pagination")
        if pagination:
            page_links = pagination.select("a.page-link:not(.next):not(.prev)")
            
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
        
        # Find grant links - adjust selector based on site structure
        grant_items = soup.select(".bando-item")  # Adjust selector
        
        for item in grant_items:
            link = item.select_one("a.bando-link")  # Adjust selector
            if link and link.has_attr("href"):
                grant_url = link["href"]
                full_url = urljoin(self.base_url, grant_url)
                urls.append(full_url)
        
        return urls
    
    def parse_grant_details(self, url: str) -> Dict[str, Any]:
        """
        Parse the details of a grant from Regione Molise.
        
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
            "Località_MR": "Molise",
            "Data creazione": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Extract grant title
        title_element = soup.select_one("h1.titolo-bando")  # Adjust selector
        if title_element:
            grant_data["Nome del bando"] = title_element.text.strip()
        
        # Extract short description
        desc_element = soup.select_one(".abstract-bando")  # Adjust selector
        if desc_element:
            grant_data["Descrizione breve (Plain text)"] = desc_element.text.strip()
        
        # Extract full description
        full_desc_element = soup.select_one(".descrizione-bando")  # Adjust selector
        if full_desc_element:
            grant_data["Descrizione del bando"] = full_desc_element.text.strip()
        
        # If we still don't have a description, use the title as a fallback
        if "Descrizione breve (Plain text)" not in grant_data and "Nome del bando" in grant_data:
            grant_data["Descrizione breve (Plain text)"] = grant_data["Nome del bando"]
        
        if "Descrizione del bando" not in grant_data and "Descrizione breve (Plain text)" in grant_data:
            grant_data["Descrizione del bando"] = grant_data["Descrizione breve (Plain text)"]
        
        # Extract deadlines
        deadline_element = soup.select_one(".data-scadenza")  # Adjust selector
        if deadline_element:
            deadline_text = deadline_element.text.strip()
            grant_data["Scadenza"] = deadline_text
            
            # Try to parse the date for internal deadline
            try:
                # Assuming Italian date format (DD/MM/YYYY)
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', deadline_text)
                if date_match:
                    grant_data["Scadenza interna"] = date_match.group(1)
            except:
                self.logger.warning(f"Could not parse deadline date: {deadline_text}")
        
        # Extract opening date
        opening_date_element = soup.select_one(".data-apertura")  # Adjust selector
        if opening_date_element:
            opening_date_text = opening_date_element.text.strip()
            grant_data["Data di apertura"] = opening_date_text
        
        # Extract eligible applicants
        eligible_element = soup.select_one(".beneficiari")  # Adjust selector
        if eligible_element:
            grant_data["A chi si rivolge"] = eligible_element.text.strip()
        
        # Extract application procedure
        procedure_element = soup.select_one(".modalita-presentazione")  # Adjust selector
        if procedure_element:
            grant_data["Iter presentazione della domanda"] = procedure_element.text.strip()
        
        # Extract grant type
        type_element = soup.select_one(".procedura-valutazione")  # Adjust selector
        if type_element:
            type_text = type_element.text.strip()
            grant_data["Tipo"] = self._map_grant_type(type_text)
        
        # Extract funding amount
        funding_element = soup.select_one(".dotazione-finanziaria")  # Adjust selector
        if funding_element:
            funding_text = funding_element.text.strip()
            # Try to extract numeric value
            amount_match = re.search(r'(\d[\d\.,]+)', funding_text)
            if amount_match:
                try:
                    # Remove commas and other non-numeric chars except decimal point
                    amount_str = re.sub(r'[^\d.]', '', amount_match.group(1).replace(',', '.'))
                    grant_data["Dotazione"] = float(amount_str)
                except:
                    self.logger.warning(f"Could not parse funding amount: {funding_text}")
        
        # Extract eligible expenses
        expenses_element = soup.select_one(".interventi-ammissibili")  # Adjust selector
        if expenses_element:
            grant_data["Spese ammissibili"] = expenses_element.text.strip()
        
        # Extract attachments
        attachments_section = soup.select_one(".documenti-bando")  # Adjust selector
        if attachments_section:
            attachments = self._extract_attachments(attachments_section)
            if attachments:
                if attachments.get("compilativi"):
                    grant_data["Allegato Compilativo - X"] = ", ".join(attachments["compilativi"])
                if attachments.get("informativi"):
                    grant_data["Allegato informativo - X"] = ", ".join(attachments["informativi"])
        
        # Extract document requirements
        full_text = self._get_full_grant_text(soup)
        doc_requirements, doc_contexts = self._extract_document_requirements(full_text)
        if doc_requirements:
            grant_data["Documentazione necessaria"] = "\n".join(f"- {doc}" for doc in doc_requirements)
        
        return grant_data
    
    def _map_grant_type(self, type_text: str) -> str:
        """
        Map the raw grant type text to standardized categories.
        
        Args:
            type_text (str): Raw grant type text
            
        Returns:
            str: Standardized grant type
        """
        type_text = type_text.lower()
        
        if any(keyword in type_text for keyword in ["sportello", "a sportello"]):
            return "Procedura a sportello"
        elif any(keyword in type_text for keyword in ["esaurimento", "fondi", "fino esaurimento"]):
            return "Esaurimento fondi"
        elif any(keyword in type_text for keyword in ["click", "clickday", "click day"]):
            return "Clickday"
        else:
            return "Data di chiusura"  # Default type
    
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
        title = soup.select_one("h1.titolo-bando")  # Adjust selector
        if title:
            text_parts.append(title.text.strip())
        
        # Get short description
        desc = soup.select_one(".abstract-bando")  # Adjust selector
        if desc:
            text_parts.append(desc.text.strip())
        
        # Get full description
        full_desc = soup.select_one(".descrizione-bando")  # Adjust selector
        if full_desc:
            text_parts.append(full_desc.text.strip())
        
        # Get eligible applicants
        eligible = soup.select_one(".beneficiari")  # Adjust selector
        if eligible:
            text_parts.append(eligible.text.strip())
        
        # Get application procedure
        procedure = soup.select_one(".modalita-presentazione")  # Adjust selector
        if procedure:
            text_parts.append(procedure.text.strip())
        
        # Get eligible expenses
        expenses = soup.select_one(".interventi-ammissibili")  # Adjust selector
        if expenses:
            text_parts.append(expenses.text.strip())
        
        # Get attachments section
        attachments = soup.select_one(".documenti-bando")  # Adjust selector
        if attachments:
            text_parts.append(attachments.text.strip())
        
        # Get any additional content sections
        content_sections = soup.select(".sezione-bando")  # Adjust selector
        for section in content_sections:
            text_parts.append(section.text.strip())
        
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