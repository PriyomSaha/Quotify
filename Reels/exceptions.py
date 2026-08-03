"""
Reel Upload Exceptions

Custom exceptions for reel upload operations.
"""

from typing import Optional, Dict, Any


class ReelUploadError(Exception):
    """Base exception for all reel upload errors."""
    pass


class VideoNotFoundError(ReelUploadError):
    """Raised when video file does not exist."""
    pass


class FacebookUploadError(ReelUploadError):
    """Raised when Facebook reel upload fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class InstagramUploadError(ReelUploadError):
    """Raised when Instagram reel upload fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class VideoNotAccessibleError(ReelUploadError):
    """Raised when public video URL is not accessible."""
    pass


class ContainerPollingError(ReelUploadError):
    """Raised when Instagram container polling fails or times out."""
    pass


class PublishError(ReelUploadError):
    """Raised when final Instagram publish step fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)
