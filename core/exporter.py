import csv
import logging
import os
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("Exporter")

class CSVExporter:
    """
    Exporter class to save grant data to CSV files.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the CSV exporter.
        
        Args:
            output_dir (str): Directory to save CSV files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export grant data to a CSV file.
        
        Args:
            data (List[Dict]): List of grant data dictionaries
            filename (str, optional): Output filename. If None, a timestamp-based name is used.
            
        Returns:
            str: Path to the saved CSV file
        """
        if not data:
            logger.warning("No data to export")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"grants_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Get all field names from the data
        fieldnames = list(data[0].keys())
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for grant in data:
                    # Convert None values to empty strings
                    sanitized_grant = {k: ('' if v is None else v) for k, v in grant.items()}
                    writer.writerow(sanitized_grant)
            
            logger.info(f"Successfully exported {len(data)} grants to {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def export_errors_to_csv(self, errors: Dict[str, List[str]], filename: str = None) -> str:
        """
        Export validation errors to a CSV file.
        
        Args:
            errors (Dict[str, List[str]]): Dictionary mapping grant IDs to lists of error messages
            filename (str, optional): Output filename. If None, a timestamp-based name is used.
            
        Returns:
            str: Path to the saved CSV file
        """
        if not errors:
            logger.warning("No errors to export")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_errors_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Grant ID", "Error Message"])
                
                for grant_id, error_list in errors.items():
                    for error in error_list:
                        writer.writerow([grant_id, error])
            
            logger.info(f"Successfully exported {sum(len(e) for e in errors.values())} errors to {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error exporting errors to CSV: {e}")
            return None