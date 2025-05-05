import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Union, Optional

logger = logging.getLogger("DataProcessor")

# Define all expected columns for the output CSV
EXPECTED_COLUMNS = [
    "Nome del bando",
    "Categoria del bando_MR",
    "Descrizione breve (Plain text)",
    "Descrizione del bando",
    "Descrizione fondo perduto",
    "Descrizione tipo di agevolazione e emanazione",
    "Dotazione",
    "Percentuale fondo perduto number",
    "Richiesta massima (number)",
    "Richiesta minima (number)",
    "Regime di aiuto",
    "Spese ammissibili",
    "Spese ammissibili_MR",
    "A chi si rivolge",
    "A chi si rivolge_MR",
    "Codice ateco",
    "Excluded Codice ateco",
    "Settore_MR",
    "Sezione",
    "Cumulabilità",
    "Scadenza",
    "Scadenza interna",
    "Data di apertura",
    "Data creazione",
    "Stato del bando",
    "Tipo",
    "Iter presentazione della domanda",
    "Documentazione necessaria",
    "Esempi progetti ammissibili",
    "Promotore del bando",
    "Emanazione",
    "Provincia",
    "Località_MR",
    "Link al sito del bando",
    "Link Bando",
    "Allegato Compilativo - X",
    "Allegato informativo - X",
]

# Known values for dropdown fields
CATEGORIAS_BANDO = [
    "credito d'imposta",
    "tasso agevolato",
    "voucher",
    "garanzia",
    "fondo perduto",
    "investimento in cambio di %",
    "tasso 0"
]

A_CHI_SI_RIVOLGE = [
    "liberi professionisti",
    "enti pubblici",
    "formatori",
    "enti del terzo settore",
    "cittadini",
    "piccola impresa",
    "fondazioni",
    "startup",
    "datori di lavoro",
    "progetto non costituito",
    "università",
    "PMI",
    "micro impresa",
    "cooperative",
    "consorzi",
    "associazioni",
    "grandi imprese"
]

SETTORE_MR = [
    "Agricoltura",
    "Consulenza",
    "Artigianato",
    "Alimentare",
    "Aiuto e supporto",
    "Cultura",
    "Istruzione",
    "Socialità",
    "Industria",
    "R&S",
    "Sostenibilità",
    "Turismo",
    "Finanziario",
    "Innovazione e digitale",
    "Servizi",
    "Sport"
]

SPESE_AMMISSIBILI_MR = [
    "Personale dipendente",
    "Personale esterno/consulenza",
    "Formazione",
    "Attrezzature e macchinari",
    "Affitto",
    "Utenze",
    "Acquisto immobili",
    "Opere edili e ristrutturazione",
    "Arredi",
    "Impianti di produzione",
    "Polizze assicurative",
    "Spese legali",
    "Spese amministrative",
    "Marketing",
    "Partecipazione a fiere ed eventi",
    "Spese di logistica",
    "Softwere",
    "Digitalizzazione",
    "Studi di fattibilità",
    "Ricerca di mercato",
    "Registrazione brevetto",
    "Registrazione marchio",
    "Certificazione",
    "Servizi",
    "Brevetti e licenze",
    "Spese generali / altri oneri",
    "Fabbricati e terreni"
]

SEZIONE_ATECO = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U']

PROMOTORE_DEL_BANDO = [
    "Invitalia",
    "Commissione Europea",
    "Ministero delle Imprese e del Made in Italy (MIMIT)",
    "Fondazioni",
    "Banca d'Italia",
    "Associazioni",
    "Regioni",
    "Camera di Commercio",
    "Ministeri",
    "Soggetti speciali"
]

EMANAZIONE = [
    "CCIAA",
    "Europeo",
    "Nazionale",
    "Regionale"
]

STATO_DEL_BANDO = [
    "Scaduto",
    "In scadenza",
    "Attivo",
    "In uscita"
]

TIPO_BANDO = [
    "Data di chiusura",
    "Procedura a sportello",
    "Esaurimento fondi",
    "Clickday"
]

LOCALITIES = [
    "Valle d'Aosta", "Piemonte", "Liguria", "Lombardia", "Veneto", 
    "Friuli Venezia Giulia", "Emilia Romagna", "Trentino Alto Adige", 
    "Abruzzo", "Molise", "Marche", "Puglia", "Calabria", "Basilicata", 
    "Sicilia", "Sardegna", "Campania", "Lazio", "Toscana", "Italia", 
    "Europa", "Mondo"
]

REGIMI_DI_AIUTO = ["De minimis", "GBER"]

def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text."""
    if text is None:
        return ""
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_number(text: Optional[str]) -> Optional[float]:
    """Extract numeric value from text."""
    if not text:
        return None
    
    # Find numbers in the text (support for both dot and comma decimal separators)
    matches = re.findall(r'(?:€\s*)?([\d.,]+)(?:\s*(?:euro|€|EUR))?', text)
    if matches:
        # Get the first match and normalize (replace comma with dot for decimal)
        value_str = matches[0].replace('.', '').replace(',', '.')
        try:
            return float(value_str)
        except ValueError:
            return None
    return None

def parse_date(date_str: Optional[str]) -> Optional[str]:
    """Parse and standardize date string."""
    if not date_str:
        return None
    
    date_str = clean_text(date_str)
    
    # Try different date formats
    date_formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
        '%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d'
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Check for common date patterns in text
    months_it = {
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
    }
    
    for month_name, month_num in months_it.items():
        if month_name in date_str.lower():
            # Try to extract day and year
            pattern = fr'(\d+)\s+{month_name}\s+(\d{{4}})'
            match = re.search(pattern, date_str.lower())
            if match:
                day, year = match.groups()
                return f"{year}-{month_num}-{day.zfill(2)}"
    
    # If we can't parse the date, return the original string
    return date_str

def match_to_controlled_vocab(text: str, vocab_list: List[str]) -> List[str]:
    """Match text to items in a controlled vocabulary list."""
    if not text:
        return []
    
    text = text.lower()
    matches = []
    
    for item in vocab_list:
        # Check if the item (or close variants) appears in the text
        if item.lower() in text or any(variant in text for variant in generate_variants(item)):
            matches.append(item)
    
    return matches

def generate_variants(term: str) -> List[str]:
    """Generate common variants of a term for better matching."""
    variants = []
    
    # Handle plural forms
    if term.endswith('e'):
        variants.append(term[:-1] + 'i')  # e.g., "imprese" -> "impresa"
    elif term.endswith('o'):
        variants.append(term[:-1] + 'i')  # e.g., "progetto" -> "progetti"
    elif term.endswith('a'):
        variants.append(term[:-1] + 'e')  # e.g., "richiesta" -> "richieste"
    
    # Handle abbreviations
    if ' ' in term:
        abbr = ''.join(word[0] for word in term.split())
        variants.append(abbr.upper())
    
    return variants

def process_grant_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and normalize raw grant data.
    
    Args:
        raw_data: Dictionary containing raw grant data
        
    Returns:
        Dictionary with processed and normalized data
    """
    processed_data = {col: "" for col in EXPECTED_COLUMNS}
    
    # Update with available data
    for key, value in raw_data.items():
        if key in processed_data:
            processed_data[key] = value
    
    # Process text fields
    for field in ["Nome del bando", "Descrizione breve (Plain text)", 
                  "Descrizione del bando", "Descrizione fondo perduto",
                  "Descrizione tipo di agevolazione e emanazione",
                  "Spese ammissibili", "A chi si rivolge",
                  "Codice ateco", "Cumulabilità", "Iter presentazione della domanda",
                  "Documentazione necessaria", "Esempi progetti ammissibili"]:
        if field in raw_data:
            processed_data[field] = clean_text(raw_data[field])
    
    # Process numeric fields
    for field in ["Dotazione", "Percentuale fondo perduto number", 
                  "Richiesta massima (number)", "Richiesta minima (number)"]:
        if field in raw_data:
            processed_data[field] = extract_number(raw_data[field])
    
    # Process date fields
    for field in ["Scadenza interna", "Data di apertura", "Data creazione"]:
        if field in raw_data:
            processed_data[field] = parse_date(raw_data[field])
    
    # Match controlled vocabulary fields
    if "A chi si rivolge" in raw_data:
        processed_data["A chi si rivolge_MR"] = ", ".join(
            match_to_controlled_vocab(raw_data["A chi si rivolge"], A_CHI_SI_RIVOLGE)
        )
    
    if "Spese ammissibili" in raw_data:
        processed_data["Spese ammissibili_MR"] = ", ".join(
            match_to_controlled_vocab(raw_data["Spese ammissibili"], SPESE_AMMISSIBILI_MR)
        )
    
    if "Descrizione del bando" in raw_data:
        processed_data["Settore_MR"] = ", ".join(
            match_to_controlled_vocab(raw_data["Descrizione del bando"], SETTORE_MR)
        )
    
    # Extract ATECO sections if available
    if "Codice ateco" in raw_data and raw_data["Codice ateco"]:
        sections = []
        for section in SEZIONE_ATECO:
            if section in raw_data["Codice ateco"] or f"sezione {section}" in raw_data["Codice ateco"].lower():
                sections.append(section)
        processed_data["Sezione"] = ", ".join(sections)
    
    return processed_data

def validate_grant_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate the grant data and return a list of validation errors.
    
    Args:
        data: Processed grant data
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Check required fields
    required_fields = [
        "Nome del bando", 
        "Descrizione breve (Plain text)",
        "Descrizione del bando",
        "Link Bando"
    ]
    
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Campo richiesto mancante: {field}")
    
    # Check URL format
    for field in ["Link al sito del bando", "Link Bando"]:
        if data.get(field) and not data[field].startswith(("http://", "https://")):
            errors.append(f"Formato URL non valido per: {field}")
    
    return errors