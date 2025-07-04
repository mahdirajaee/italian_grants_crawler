import os
from typing import Dict, Any, List

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Request settings
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_DELAY = 2.0  # seconds between requests
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_PAGES_PER_SITE = 100

# User agent rotation (to avoid getting blocked)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

# Website configurations
REGIONAL_SITES = {
    "vda": {
        "name": "Valle d'Aosta",
        "base_url": "https://www.regione.vda.it",
        "grants_url": "/bandi",
        "selectors": {
            "list_items": ".views-row",
            "link": "a",
            "title": "h2",
        }
    },
    "piemonte": {
        "name": "Piemonte",
        "base_url": "https://bandi.regione.piemonte.it",
        "grants_url": "/",
        "selectors": {
            "list_items": ".view-content .views-row",
            "link": "a",
            "title": "h2",
        }
    },
    "lombardia": {
        "name": "Lombardia",
        "base_url": "https://www.bandi.regione.lombardia.it",
        "grants_url": "/servizi/servizio/bandi",
        "selectors": {
            "list_items": ".card.card-bg.card-big",
            "link": "a:contains('Scopri di più')",
            "title": "h1",
        }
    },
    "veneto": {
        "name": "Veneto",
        "base_url": "https://bandi.regione.veneto.it",
        "grants_url": "/web/guest/bandi-finanziamenti-e-avvisi",
        "selectors": {
            "list_items": ".item-list",
            "link": "a",
            "title": "h3",
        }
    },
    "liguria": {
        "name": "Liguria",
        "base_url": "https://www.regione.liguria.it",
        "grants_url": "/it/bandi-e-avvisi",
        "selectors": {
            "list_items": ".card-wrapper",
            "link": "a",
            "title": "h3",
        }
    },
    "emilia_romagna": {
        "name": "Emilia Romagna",
        "base_url": "https://bandi.regione.emilia-romagna.it",
        "grants_url": "/it/ricerca-bandi",
        "selectors": {
            "list_items": ".item",
            "link": "a",
            "title": "h3",
        }
    },
    "trentino_alto_adige": {
        "name": "Trentino Alto Adige",
        "base_url": "https://www.regione.taa.it",
        "grants_url": "/it/bandi",
        "selectors": {
            "list_items": ".article",
            "link": "a",
            "title": "h2",
        }
    },
    "friuli_venezia_giulia": {
        "name": "Friuli Venezia Giulia",
        "base_url": "https://www.regione.fvg.it",
        "grants_url": "/it/web/guest/contributi-avvisi-bandi-gare",
        "selectors": {
            "list_items": ".card",
            "link": "a",
            "title": "h3",
        }
    },
    "toscana": {
        "name": "Toscana",
        "base_url": "https://www.regione.toscana.it",
        "grants_url": "/-/bandi-e-avvisi-attivi",
        "selectors": {
            "list_items": ".list-item",
            "link": "a",
            "title": "h3",
        }
    },
    "umbria": {
        "name": "Umbria",
        "base_url": "https://www.regione.umbria.it",
        "grants_url": "/it/bandi",
        "selectors": {
            "list_items": ".item",
            "link": "a",
            "title": "h3",
        }
    },
    "marche": {
        "name": "Marche",
        "base_url": "https://www.regione.marche.it",
        "grants_url": "/regione-utile/opportunita-sviluppo/bandi-di-finanziamento",
        "selectors": {
            "list_items": ".content-item",
            "link": "a",
            "title": "h3",
        }
    },
    "lazio": {
        "name": "Lazio",
        "base_url": "https://www.regione.lazio.it",
        "grants_url": "/web/guest/bandi-e-avvisi",
        "selectors": {
            "list_items": ".card",
            "link": "a",
            "title": "h3",
        }
    },
    "abruzzo": {
        "name": "Abruzzo",
        "base_url": "https://www.regione.abruzzo.it",
        "grants_url": "/content/bandi-aperti",
        "selectors": {
            "list_items": ".view-content .views-row",
            "link": "a",
            "title": "h2",
        }
    },
    "molise": {
        "name": "Molise",
        "base_url": "https://www3.regione.molise.it",
        "grants_url": "/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/16881",
        "selectors": {
            "list_items": ".elenco_allegati",
            "link": "a",
            "title": "span",
        }
    },
    "campania": {
        "name": "Campania",
        "base_url": "https://www.regione.campania.it",
        "grants_url": "/tematiche/attivita-economiche/bandi",
        "selectors": {
            "list_items": ".item",
            "link": "a",
            "title": "h4",
        }
    },
    "puglia": {
        "name": "Puglia",
        "base_url": "https://www.regione.puglia.it",
        "grants_url": "/web/guest/bandi-e-avvisi",
        "selectors": {
            "list_items": ".item",
            "link": "a",
            "title": "h2",
        }
    },
    "basilicata": {
        "name": "Basilicata",
        "base_url": "https://www.regione.basilicata.it",
        "grants_url": "/giunta/site/giunta/department.jsp?dep=100435&area=3052459",
        "selectors": {
            "list_items": ".list-item",
            "link": "a",
            "title": "h3",
        }
    },
    "calabria": {
        "name": "Calabria",
        "base_url": "https://www.regione.calabria.it",
        "grants_url": "/bandi",
        "selectors": {
            "list_items": ".list-item",
            "link": "a",
            "title": "h3",
        }
    },
    "sicilia": {
        "name": "Sicilia",
        "base_url": "https://www.regione.sicilia.it",
        "grants_url": "/istituzioni/regione/strutture-regionali/presidenza/dipartimento-della-programmazione/bandi-e-avvisi",
        "selectors": {
            "list_items": ".list-item",
            "link": "a",
            "title": "h3",
        }
    },
    "sardegna": {
        "name": "Sardegna",
        "base_url": "https://www.regione.sardegna.it",
        "grants_url": "/it/bandi-e-gare",
        "selectors": {
            "list_items": ".article",
            "link": "a",
            "title": "h3",
        }
    }
}

COMMERCE_SITES = {
    "to_camcom": {
        "name": "Camera di Commercio di Torino",
        "base_url": "https://www.to.camcom.it",
        "grants_url": "/bandi",
        "selectors": {
            "list_items": ".list-item",
            "link": "a.title",
            "title": "h2",
        }
    },
    "milomb_camcom": {
        "name": "Camera di Commercio di Milano Monza Brianza Lodi",
        "base_url": "https://www.milomb.camcom.it",
        "grants_url": "/bandi-contributi",
        "selectors": {
            "list_items": ".views-row",
            "link": "a",
            "title": "h3",
        }
    },
    # Add other chambers of commerce here
}

NATIONAL_SITES = {
    "invitalia": {
        "name": "Invitalia",
        "base_url": "https://www.invitalia.it",
        "grants_url": "/cosa-facciamo/rafforziamo-le-imprese/incentivi",
        "selectors": {
            "list_items": ".box-incentivo",
            "link": "a",
            "title": "h2",
        }
    },
    "mimit": {
        "name": "Ministero delle Imprese e del Made in Italy",
        "base_url": "https://www.mimit.gov.it",
        "grants_url": "/it/incentivi/",
        "selectors": {
            "list_items": ".scheda",
            "link": "a",
            "title": "h3",
        }
    },
    # Add other national sites here
}

# Expected CSV structure
CSV_COLUMNS = [
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

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "simple": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": os.path.join(LOG_DIR, "crawler.log"),
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

# List of provinces by region
PROVINCES_BY_REGION = {
    "Valle d'Aosta": ["Aosta"],
    "Piemonte": ["Torino", "Alessandria", "Asti", "Biella", "Cuneo", "Novara", "Verbano-Cusio-Ossola", "Vercelli"],
    "Liguria": ["Genova", "Imperia", "La Spezia", "Savona"],
    "Lombardia": ["Milano", "Bergamo", "Brescia", "Como", "Cremona", "Lecco", "Lodi", "Mantova", "Monza e Brianza", "Pavia", "Sondrio", "Varese"],
    "Veneto": ["Venezia", "Belluno", "Padova", "Rovigo", "Treviso", "Verona", "Vicenza"],
    "Friuli-Venezia Giulia": ["Trieste", "Gorizia", "Pordenone", "Udine"],
    "Emilia-Romagna": ["Bologna", "Ferrara", "Forlì-Cesena", "Modena", "Parma", "Piacenza", "Ravenna", "Reggio Emilia", "Rimini"],
    "Trentino-Alto Adige": ["Trento", "Bolzano"],
    "Toscana": ["Firenze", "Arezzo", "Grosseto", "Livorno", "Lucca", "Massa-Carrara", "Pisa", "Pistoia", "Prato", "Siena"],
    "Umbria": ["Perugia", "Terni"],
    "Marche": ["Ancona", "Ascoli Piceno", "Fermo", "Macerata", "Pesaro e Urbino"],
    "Lazio": ["Roma", "Frosinone", "Latina", "Rieti", "Viterbo"],
    "Abruzzo": ["L'Aquila", "Chieti", "Pescara", "Teramo"],
    "Molise": ["Campobasso", "Isernia"],
    "Campania": ["Napoli", "Avellino", "Benevento", "Caserta", "Salerno"],
    "Puglia": ["Bari", "Barletta-Andria-Trani", "Brindisi", "Foggia", "Lecce", "Taranto"],
    "Basilicata": ["Potenza", "Matera"],
    "Calabria": ["Catanzaro", "Cosenza", "Crotone", "Reggio Calabria", "Vibo Valentia"],
    "Sicilia": ["Palermo", "Agrigento", "Caltanissetta", "Catania", "Enna", "Messina", "Ragusa", "Siracusa", "Trapani"],
    "Sardegna": ["Cagliari", "Nuoro", "Oristano", "Sassari", "Sud Sardegna"]
}