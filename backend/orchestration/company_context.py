"""
company_context.py - Company context manager for multi-tenancy

This module manages the current company context for multi-tenant operations.
For the demo, this is hardcoded to "xai" (xAI).

Implementation Rationale:

Why a context manager:
1. **Multi-tenancy**: All queries must be filtered by company_id
2. **Automatic injection**: Context manager ensures company_id is always included
3. **Demo simplicity**: Hardcoded to "xai" for now, can be extended later

Design Decisions:
- **Hardcoded for demo**: Current company is always "xai"
- **Helper methods**: Provide utilities for filtering queries
- **Future extension**: Can add authentication/user context later
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CompanyContext:
    """
    Manages current company context for multi-tenant operations.
    
    For demo purposes, this is hardcoded to "xai" (xAI).
    All database queries should filter by company_id to ensure data isolation.
    """
    
    def __init__(self, company_id: Optional[str] = None):
        """
        Initialize company context.
        
        Args:
            company_id: Company ID. Defaults to "xai" for demo.
        """
        self.current_company_id = company_id or "xai"
        logger.info(f"Company context initialized: {self.current_company_id}")
    
    def get_company_id(self) -> str:
        """
        Get current company ID.
        
        Returns:
            Current company ID (default: "xai")
        """
        return self.current_company_id
    
    def filter_by_company(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add company_id filter to query parameters.
        
        Args:
            query_params: Dictionary of query parameters
        
        Returns:
            Query parameters with company_id added
        """
        query_params['company_id'] = self.current_company_id
        return query_params
    
    def add_company_to_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add company_id to metadata dictionary.
        
        Args:
            metadata: Metadata dictionary
        
        Returns:
            Metadata with company_id added
        """
        metadata['company_id'] = self.current_company_id
        return metadata
    
    def ensure_company_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure company_id exists in data dictionary.
        If missing, adds it. If present, validates it matches current company.
        
        Args:
            data: Data dictionary
        
        Returns:
            Data dictionary with company_id ensured
        
        Raises:
            ValueError: If data has a different company_id than current context
        """
        if 'company_id' in data:
            if data['company_id'] != self.current_company_id:
                raise ValueError(
                    f"Data company_id ({data['company_id']}) does not match "
                    f"current context ({self.current_company_id})"
                )
        else:
            data['company_id'] = self.current_company_id
        
        return data


# Global company context instance (hardcoded to "xai" for demo)
_company_context = CompanyContext()


def get_company_context() -> CompanyContext:
    """
    Get the global company context instance.
    
    Returns:
        CompanyContext instance (hardcoded to "xai" for demo)
    """
    return _company_context

