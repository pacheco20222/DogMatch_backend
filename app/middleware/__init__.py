"""
Middleware package for DogMatch application.

This package contains middleware components for request/response processing.
"""

from .request_logger import log_request, log_response

__all__ = ['log_request', 'log_response']
