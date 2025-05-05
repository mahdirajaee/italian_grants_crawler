import re
import logging
from typing import Optional, List, Dict, Any, Union
from bs4 import BeautifulSoup, Tag, NavigableString

logger = logging.getLogger("HTMLParser")

def get_text_from_selector(soup: BeautifulSoup, selector: str) -> str:
    """
    Extract text from an element selected by CSS selector.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        selector (str): CSS selector
        
    Returns:
        str: Extracted text or empty string if not found
    """
    element = soup.select_one(selector)
    if element:
        return element.get_text(strip=True)
    return ""

def get_attr_from_selector(soup: BeautifulSoup, selector: str, attr: str) -> str:
    """
    Extract attribute from an element selected by CSS selector.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        selector (str): CSS selector
        attr (str): Attribute name
        
    Returns:
        str: Attribute value or empty string if not found
    """
    element = soup.select_one(selector)
    if element and element.has_attr(attr):
        return element[attr]
    return ""

def get_elements_with_text(soup: BeautifulSoup, pattern: str, tag_name: Optional[str] = None) -> List[Tag]:
    """
    Find elements containing text matching a pattern.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        pattern (str): Regular expression pattern to match
        tag_name (str, optional): Specific tag to look for
        
    Returns:
        List[Tag]: List of matching elements
    """
    if tag_name:
        elements = soup.find_all(tag_name)
    else:
        elements = soup.find_all(True)  # Find all tags
    
    return [el for el in elements if el.string and re.search(pattern, el.string, re.IGNORECASE)]

def extract_table_data(table: Tag) -> List[Dict[str, str]]:
    """
    Extract data from an HTML table into a list of dictionaries.
    
    Args:
        table (Tag): BeautifulSoup Tag representing an HTML table
        
    Returns:
        List[Dict[str, str]]: List of dictionaries with column names as keys
    """
    if not table:
        return []
    
    data = []
    headers = []
    
    # Extract headers
    thead = table.find('thead')
    if thead:
        header_cells = thead.find_all('th')
        headers = [cell.get_text(strip=True) for cell in header_cells]
    
    if not headers and table.find('tr'):
        # Try to get headers from first row if no thead
        first_row = table.find('tr')
        header_cells = first_row.find_all(['th', 'td'])
        headers = [cell.get_text(strip=True) for cell in header_cells]
        rows = table.find_all('tr')[1:]  # Skip the header row
    else:
        # Get all rows for data
        rows = table.find_all('tr')
        if thead:
            # Filter out header row if we found headers in thead
            rows = [row for row in rows if row.parent != thead]
    
    # Process rows
    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) == 0:
            continue
            
        if not headers:
            # If we still don't have headers, use indices as keys
            row_data = {f"col_{i}": cell.get_text(strip=True) for i, cell in enumerate(cells)}
        elif len(cells) == len(headers):
            # One-to-one mapping of headers to cells
            row_data = {headers[i]: cell.get_text(strip=True) for i, cell in enumerate(cells) if i < len(headers)}
        else:
            # Mismatch in number of header/data cells, use available headers and index rest
            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row_data[headers[i]] = cell.get_text(strip=True)
                else:
                    row_data[f"col_{i}"] = cell.get_text(strip=True)
        
        data.append(row_data)
    
    return data

def get_next_section_after_heading(soup: BeautifulSoup, heading_text: str, heading_tag: Optional[str] = None, max_elements: int = 5) -> List[Tag]:
    """
    Get elements that appear after a heading with the specified text.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        heading_text (str): Text to search for in headings
        heading_tag (str, optional): Specific heading tag (h1, h2, etc.) to look for
        max_elements (int): Maximum number of elements to return
        
    Returns:
        List[Tag]: Elements following the heading
    """
    # Find the heading
    if heading_tag:
        heading = soup.find(heading_tag, string=re.compile(heading_text, re.IGNORECASE))
    else:
        heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], string=re.compile(heading_text, re.IGNORECASE))
    
    if not heading:
        return []
    
    # Collect elements that follow the heading
    elements = []
    current = heading.next_sibling
    
    while current and len(elements) < max_elements:
        if isinstance(current, Tag) and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements.append(current)
        elif isinstance(current, NavigableString) and current.strip():
            # Include non-empty text nodes
            elements.append(current)
        
        current = current.next_sibling
    
    return elements

def extract_structured_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract structured data from meta tags, JSON-LD, or other structured formats.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        Dict[str, Any]: Extracted structured data
    """
    data = {}
    
    # Check for JSON-LD script
    ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
    for script in ld_scripts:
        try:
            import json
            script_data = json.loads(script.string)
            data.update({"json_ld": script_data})
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse JSON-LD data")
    
    # Check for meta tags
    meta_tags = {}
    for meta in soup.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            meta_tags[meta['name']] = meta['content']
        elif meta.has_attr('property') and meta.has_attr('content'):
            meta_tags[meta['property']] = meta['content']
    
    if meta_tags:
        data.update({"meta_tags": meta_tags})
    
    return data

def extract_links(soup: BeautifulSoup, base_url: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract all links from the page, categorized by type.
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        base_url (str): Base URL for resolving relative links
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Categorized links
    """
    from urllib.parse import urljoin
    
    categorized_links = {
        "pdf": [],
        "doc": [],
        "image": [],
        "external": [],
        "internal": [],
        "other": []
    }
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        link_text = link.get_text(strip=True)
        
        link_data = {
            "url": full_url,
            "text": link_text,
            "original_href": href
        }
        
        # Categorize the link
        if href.startswith(('http://', 'https://')) and base_url not in href:
            categorized_links["external"].append(link_data)
        elif href.lower().endswith('.pdf'):
            categorized_links["pdf"].append(link_data)
        elif href.lower().endswith(('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
            categorized_links["doc"].append(link_data)
        elif href.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')):
            categorized_links["image"].append(link_data)
        elif href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            categorized_links["other"].append(link_data)
        else:
            categorized_links["internal"].append(link_data)
    
    return categorized_links

def find_date_in_text(text: str) -> Optional[str]:
    """
    Find date patterns in text.
    
    Args:
        text (str): Text to search for dates
        
    Returns:
        Optional[str]: Found date or None
    """
    # Common Italian date formats
    patterns = [
        r'\b(\d{1,2})[/\.-](\d{1,2})[/\.-](\d{2,4})\b',  # DD/MM/YYYY, DD.MM.YYYY, DD-MM-YYYY
        r'\b(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})\b',  # DD Month YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None