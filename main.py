#!/usr/bin/env python3
import os
import argparse
import logging
import logging.config
import importlib
import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime

import config
from core.data_processor import process_grant_data, validate_grant_data
from core.exporter import CSVExporter

# Import crawlers
from crawlers.regional.lombardia_crawler import LombardiaCrawler
# Import other crawlers as you implement them


def setup_logging():
    """Set up logging configuration."""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logging.config.dictConfig(config.LOGGING_CONFIG)


def get_crawler_class(site_type: str, site_name: str) -> Optional[type]:
    """
    Dynamically import and return the crawler class for a specific site.
    
    Args:
        site_type (str): Type of site (regional, commerce, national)
        site_name (str): Name of the site
        
    Returns:
        Optional[type]: Crawler class or None if not found
    """
    try:
        module_name = f"crawlers.{site_type}.{site_name}_crawler"
        module = importlib.import_module(module_name)
        
        # Find the crawler class in the module (assuming it ends with "Crawler")
        for attr_name in dir(module):
            if attr_name.endswith("Crawler") and attr_name != "BaseCrawler":
                return getattr(module, attr_name)
        
        logging.error(f"No crawler class found in module {module_name}")
        return None
    
    except ImportError as e:
        logging.error(f"Could not import crawler for {site_type}.{site_name}: {e}")
        return None


def crawl_site(site_type: str, site_name: str, max_pages: int = 10) -> List[Dict[str, Any]]:
    """
    Crawl a specific site for grants.
    
    Args:
        site_type (str): Type of site (regional, commerce, national)
        site_name (str): Name of the site
        max_pages (int): Maximum number of grant pages to crawl
        
    Returns:
        List[Dict[str, Any]]: List of grant data dictionaries
    """
    logger = logging.getLogger(f"crawl_site.{site_type}.{site_name}")
    
    # Get crawler class
    crawler_class = get_crawler_class(site_type, site_name)
    if not crawler_class:
        logger.error(f"No crawler implementation found for {site_type}.{site_name}")
        return []
    
    # Get site configuration
    site_config = None
    if site_type == "regional":
        site_config = config.REGIONAL_SITES.get(site_name)
    elif site_type == "commerce":
        site_config = config.COMMERCE_SITES.get(site_name)
    elif site_type == "national":
        site_config = config.NATIONAL_SITES.get(site_name)
    
    if not site_config:
        logger.error(f"No configuration found for {site_type}.{site_name}")
        return []
    
    try:
        # Initialize crawler
        crawler = crawler_class(max_pages=max_pages)
        
        # Crawl site
        logger.info(f"Starting to crawl {site_config['name']} ({site_config['base_url']})")
        grants = crawler.crawl()
        
        # Process and validate grant data
        processed_grants = []
        validation_errors = {}
        
        for i, grant in enumerate(grants):
            # Process grant data
            processed_grant = process_grant_data(grant)
            
            # Validate
            errors = validate_grant_data(processed_grant)
            if errors:
                grant_id = processed_grant.get("Nome del bando", f"Grant_{i}")
                validation_errors[grant_id] = errors
                logger.warning(f"Validation errors for {grant_id}: {', '.join(errors)}")
            
            processed_grants.append(processed_grant)
        
        logger.info(f"Finished crawling {site_config['name']}: {len(processed_grants)} grants found")
        
        return processed_grants
    
    except Exception as e:
        logger.error(f"Error crawling {site_type}.{site_name}: {e}", exc_info=True)
        return []


def run_crawler(args):
    """Run the crawler with the provided arguments."""
    setup_logging()
    logger = logging.getLogger("main")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exporter = CSVExporter(output_dir=config.OUTPUT_DIR)
    
    # Collect all sites to crawl
    sites_to_crawl = []
    
    if args.regional:
        for site_name in config.REGIONAL_SITES:
            if args.sites and site_name not in args.sites:
                continue
            sites_to_crawl.append(("regional", site_name))
    
    if args.commerce:
        for site_name in config.COMMERCE_SITES:
            if args.sites and site_name not in args.sites:
                continue
            sites_to_crawl.append(("commerce", site_name))
    
    if args.national:
        for site_name in config.NATIONAL_SITES:
            if args.sites and site_name not in args.sites:
                continue
            sites_to_crawl.append(("national", site_name))
    
    # If no category specified, crawl all sites
    if not (args.regional or args.commerce or args.national):
        for site_name in config.REGIONAL_SITES:
            if args.sites and site_name not in args.sites:
                continue
            sites_to_crawl.append(("regional", site_name))
        
        for site_name in config.COMMERCE_SITES:
            if args.sites and site_name not in args.sites:
                continue
            sites_to_crawl.append(("commerce", site_name))
        
        for site_name in config.NATIONAL_SITES:
            if args.sites and site_name not in args.sites:
                continue
            sites_to_crawl.append(("national", site_name))
    
    logger.info(f"Preparing to crawl {len(sites_to_crawl)} sites")
    
    all_grants = []
    
    # Use parallel processing if enabled
    if args.parallel and args.max_workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            # Submit crawling tasks
            future_to_site = {
                executor.submit(crawl_site, site_type, site_name, args.max_pages): (site_type, site_name)
                for site_type, site_name in sites_to_crawl
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_site):
                site_type, site_name = future_to_site[future]
                try:
                    grants = future.result()
                    all_grants.extend(grants)
                    logger.info(f"Completed crawling {site_type}.{site_name}: {len(grants)} grants")
                except Exception as e:
                    logger.error(f"Exception crawling {site_type}.{site_name}: {e}")
    else:
        # Sequential processing
        for site_type, site_name in sites_to_crawl:
            grants = crawl_site(site_type, site_name, args.max_pages)
            all_grants.extend(grants)
    
    # Export all grants to CSV
    if all_grants:
        output_file = f"grants_{timestamp}.csv"
        if args.output:
            output_file = args.output
        
        filepath = exporter.export_to_csv(all_grants, filename=output_file)
        logger.info(f"Exported {len(all_grants)} grants to {filepath}")
    else:
        logger.warning("No grants found to export")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Italian Grants Crawler")
    
    # Site selection arguments
    parser.add_argument("--regional", action="store_true", help="Crawl regional government sites")
    parser.add_argument("--commerce", action="store_true", help="Crawl chamber of commerce sites")
    parser.add_argument("--national", action="store_true", help="Crawl national institution sites")
    parser.add_argument("--sites", nargs="+", help="Specific sites to crawl (site codes, e.g. 'lombardia vda')")
    
    # Crawling parameters
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of grant pages to crawl per site")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of worker threads for parallel processing")
    
    # Output options
    parser.add_argument("--output", type=str, help="Output CSV filename")
    
    args = parser.parse_args()
    run_crawler(args)