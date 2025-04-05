"""
Lead Parser Module

This module provides functionality for parsing lead data from various sources.
"""

import csv
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ..models.base_models import Lead, LeadSource
from ..utils.utils import generate_id, logger

class LeadParser(ABC):
    """
    Abstract base class for lead parsers.
    
    This class defines the interface for all lead parsers.
    """
    
    @abstractmethod
    def parse_source(self, source_path: str) -> List[Lead]:
        """
        Parse the source and return a list of leads.
        
        Args:
            source_path: Path to the source
            
        Returns:
            A list of Lead objects
        """
        pass
    
    def validate_data(self, lead_data: Dict[str, Any]) -> bool:
        """
        Validate lead data.
        
        Args:
            lead_data: The lead data to validate
            
        Returns:
            True if the data is valid, False otherwise
        """
        # Check required fields
        required_fields = ["first_name", "last_name", "email", "company_name"]
        for field in required_fields:
            if field not in lead_data or not lead_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate email format (basic check)
        email = lead_data.get("email", "")
        if not "@" in email or not "." in email:
            logger.warning(f"Invalid email format: {email}")
            return False
        
        return True
    
    def transform_to_standard_format(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw data to standard format.
        
        Args:
            raw_data: The raw data to transform
            
        Returns:
            Standardized data
        """
        # Create a new dictionary with standardized keys
        standardized = {}
        
        # Map common field variations to standard fields
        field_mappings = {
            "first_name": ["first_name", "firstname", "fname", "first"],
            "last_name": ["last_name", "lastname", "lname", "last"],
            "email": ["email", "email_address", "emailaddress"],
            "company_name": ["company_name", "company", "organization", "org"],
            "job_title": ["job_title", "title", "position", "role"],
            "industry": ["industry", "sector"],
            "company_size": ["company_size", "size", "employees", "employee_count"],
            "phone": ["phone", "phone_number", "phonenumber", "telephone"],
            "website": ["website", "web", "url", "site"],
            "pain_points": ["pain_points", "painpoints", "challenges", "problems"],
            "interests": ["interests", "topics", "focus_areas"],
            "notes": ["notes", "comments", "additional_info"]
        }
        
        # Process each standard field
        for standard_field, variations in field_mappings.items():
            for variation in variations:
                if variation in raw_data and raw_data[variation]:
                    # Handle list fields
                    if standard_field in ["pain_points", "interests"] and isinstance(raw_data[variation], str):
                        # Split comma-separated string into list
                        standardized[standard_field] = [item.strip() for item in raw_data[variation].split(",")]
                    else:
                        standardized[standard_field] = raw_data[variation]
                    break
        
        # Add any custom fields not in standard mappings
        standardized["custom_fields"] = {}
        for key, value in raw_data.items():
            is_standard = False
            for variations in field_mappings.values():
                if key in variations:
                    is_standard = True
                    break
            
            if not is_standard and value:
                standardized["custom_fields"][key] = value
        
        return standardized


class CSVLeadParser(LeadParser):
    """
    Parser for CSV files.
    """
    
    def parse_source(self, source_path: str) -> List[Lead]:
        """
        Parse a CSV file and return a list of leads.
        
        Args:
            source_path: Path to the CSV file
            
        Returns:
            A list of Lead objects
        """
        logger.info(f"Parsing CSV file: {source_path}")
        
        leads = []
        
        try:
            # Read CSV file using pandas
            df = pd.read_csv(source_path)
            
            # Convert DataFrame to list of dictionaries
            raw_leads = df.to_dict(orient="records")
            
            # Process each lead
            for raw_lead in raw_leads:
                # Transform to standard format
                standardized = self.transform_to_standard_format(raw_lead)
                
                # Validate the data
                if not self.validate_data(standardized):
                    logger.warning(f"Skipping invalid lead: {standardized}")
                    continue
                
                # Create Lead object
                try:
                    lead = Lead(
                        id=generate_id("lead"),
                        first_name=standardized.get("first_name", ""),
                        last_name=standardized.get("last_name", ""),
                        email=standardized.get("email", ""),
                        company_name=standardized.get("company_name", ""),
                        job_title=standardized.get("job_title"),
                        industry=standardized.get("industry"),
                        company_size=standardized.get("company_size"),
                        phone=standardized.get("phone"),
                        website=standardized.get("website"),
                        source=LeadSource.CSV,
                        pain_points=standardized.get("pain_points", []),
                        interests=standardized.get("interests", []),
                        notes=standardized.get("notes", ""),
                        custom_fields=standardized.get("custom_fields", {})
                    )
                    leads.append(lead)
                except Exception as e:
                    logger.error(f"Error creating lead: {e}")
            
            logger.info(f"Successfully parsed {len(leads)} leads from {source_path}")
            return leads
        
        except Exception as e:
            logger.error(f"Error parsing CSV file {source_path}: {e}")
            return []


class PDFLeadParser(LeadParser):
    """
    Parser for PDF files.
    
    Note: This is a placeholder implementation. In a real system, this would use
    a library like pdfplumber to extract text from PDFs and then parse the text.
    """
    
    def parse_source(self, source_path: str) -> List[Lead]:
        """
        Parse a PDF file and return a list of leads.
        
        Args:
            source_path: Path to the PDF file
            
        Returns:
            A list of Lead objects
        """
        logger.info(f"Parsing PDF file: {source_path}")
        
        # This is a placeholder implementation
        logger.warning("PDF parsing not fully implemented yet")
        
        # In a real implementation, this would:
        # 1. Use pdfplumber to extract text from the PDF
        # 2. Parse the text to identify lead information
        # 3. Create Lead objects from the parsed information
        
        return []


class APILeadParser(LeadParser):
    """
    Parser for API data.
    
    Note: This is a placeholder implementation. In a real system, this would
    connect to an API, retrieve data, and parse it.
    """
    
    def parse_source(self, source_path: str) -> List[Lead]:
        """
        Parse API data and return a list of leads.
        
        Args:
            source_path: API endpoint or configuration file
            
        Returns:
            A list of Lead objects
        """
        logger.info(f"Parsing API data from: {source_path}")
        
        # This is a placeholder implementation
        logger.warning("API parsing not fully implemented yet")
        
        # In a real implementation, this would:
        # 1. Connect to the API specified in source_path
        # 2. Retrieve lead data
        # 3. Parse the data and create Lead objects
        
        return []


def create_lead_parser(source_type: str) -> LeadParser:
    """
    Factory function to create a lead parser based on source type.
    
    Args:
        source_type: The type of source to parse
        
    Returns:
        A LeadParser instance
        
    Raises:
        ValueError: If the source type is not supported
    """
    if source_type.lower() == "csv":
        return CSVLeadParser()
    elif source_type.lower() == "pdf":
        return PDFLeadParser()
    elif source_type.lower() == "api":
        return APILeadParser()
    else:
        raise ValueError(f"Unsupported source type: {source_type}")
