"""
Service manager for handling application services.
"""
from typing import Dict, Any, Optional
from flask import Flask

from .s3_service import S3Service, create_s3_service
from .meshroom_service import MeshroomService
from ..logger import get_logger

logger = get_logger('service_manager')


class ServiceManager:
    """Manages application services."""
    
    def __init__(self, app: Flask):
        self.app = app
        self.services: Dict[str, Any] = {}
    
    def init_services(self):
        """Initialize all services."""
        try:
            # Initialize S3 service
            self._init_s3_service()
            
            # Initialize Meshroom service
            self._init_meshroom_service()
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _init_s3_service(self):
        """Initialize S3 service."""
        try:
            s3_service = create_s3_service(self.app.config)
            if s3_service:
                self.services['s3'] = s3_service
                logger.info("S3 service initialized")
            else:
                logger.warning("S3 service not configured - S3 features disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            # Don't raise - S3 is optional
    
    def _init_meshroom_service(self):
        """Initialize Meshroom service."""
        try:
            meshroom_service = MeshroomService(self.app.config)
            self.services['meshroom'] = meshroom_service
            logger.info("Meshroom service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Meshroom service: {e}")
            raise
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get service by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance or None
        """
        return self.services.get(service_name)
    
    def has_service(self, service_name: str) -> bool:
        """
        Check if service is available.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if service is available
        """
        return service_name in self.services
    
    def list_services(self) -> list:
        """List available services."""
        return list(self.services.keys())
    
    def cleanup(self):
        """Cleanup all services."""
        try:
            for service_name, service in self.services.items():
                if hasattr(service, 'cleanup'):
                    service.cleanup()
                logger.info(f"Service {service_name} cleaned up")
                
        except Exception as e:
            logger.error(f"Service cleanup failed: {e}")
