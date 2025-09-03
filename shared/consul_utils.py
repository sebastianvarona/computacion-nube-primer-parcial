"""
Consul integration utility for microservices
Provides service registration, discovery, and health check functionality
"""
import os
import consul
import socket
import atexit
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class ConsulClient:
    def __init__(self, host: str = None, port: int = None):
        """Initialize Consul client with environment variables or defaults"""
        self.consul_host = host or os.getenv('CONSUL_HOST', 'localhost')
        self.consul_port = port or int(os.getenv('CONSUL_PORT', '8500'))
        
        try:
            self.consul = consul.Consul(host=self.consul_host, port=self.consul_port)
            logger.info(f"Connected to Consul at {self.consul_host}:{self.consul_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Consul: {e}")
            raise

    def register_service(self, service_name: str, service_port: int, 
                        health_check_url: str = None, tags: List[str] = None) -> bool:
        """Register a service with Consul"""
        try:
            # Get container IP address and hostname
            hostname = socket.gethostname()
            service_id = f"{service_name}-{hostname}"
            
            # Try to get the actual IP address that's accessible within the Docker network
            try:
                # Get the IP address by connecting to the Consul server
                import socket as sock
                s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
                s.connect((self.consul_host, self.consul_port))
                service_address = s.getsockname()[0]
                s.close()
            except Exception:
                # Fallback to hostname if IP detection fails
                service_address = hostname
            
            # Prepare health check with the service address
            check = None
            if health_check_url:
                # Use the detected IP address for health check URL
                if not health_check_url.startswith('http'):
                    health_check_url = f"http://{service_address}:{service_port}{health_check_url}"
                else:
                    # Replace hostname with IP in the URL if it contains hostname
                    health_check_url = health_check_url.replace(f"http://{hostname}:", f"http://{service_address}:")
                check = consul.Check.http(health_check_url, interval="30s", timeout="10s")
            
            # Register service
            self.consul.agent.service.register(
                name=service_name,
                service_id=service_id,
                address=service_address,
                port=service_port,
                tags=tags or [],
                check=check
            )
            
            logger.info(f"Service {service_name} registered with ID {service_id} at {service_address}:{service_port}")
            
            # Register cleanup on exit
            atexit.register(self.deregister_service, service_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {e}")
            return False

    def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from Consul"""
        try:
            self.consul.agent.service.deregister(service_id)
            logger.info(f"Service {service_id} deregistered")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {e}")
            return False

    def discover_service(self, service_name: str) -> Optional[Dict]:
        """Discover a service by name and return its connection details"""
        try:
            services = self.consul.health.service(service_name, passing=True)[1]
            if not services:
                logger.warning(f"No healthy instances found for service {service_name}")
                return None
            
            # Return the first healthy instance
            service = services[0]['Service']
            return {
                'host': service['Address'],
                'port': service['Port'],
                'service_id': service['ID'],
                'tags': service.get('Tags', [])
            }
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {e}")
            return None

    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get HTTP URL for a service"""
        service_info = self.discover_service(service_name)
        if service_info:
            return f"http://{service_info['host']}:{service_info['port']}"
        return None

    def list_services(self) -> Dict:
        """List all registered services"""
        try:
            return self.consul.agent.services()
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return {}

    def health_check(self) -> bool:
        """Check if Consul is healthy"""
        try:
            self.consul.agent.checks()
            return True
        except Exception as e:
            logger.error(f"Consul health check failed: {e}")
            return False


# Global instance for easy import
consul_client = None

def get_consul_client() -> ConsulClient:
    """Get or create global Consul client instance"""
    global consul_client
    if consul_client is None:
        consul_client = ConsulClient()
    return consul_client

def register_service_with_consul(service_name: str, service_port: int, 
                                health_endpoint: str = "/health") -> bool:
    """Helper function to register service with health check"""
    try:
        client = get_consul_client()
        health_url = f"http://{socket.gethostname()}:{service_port}{health_endpoint}"
        return client.register_service(service_name, service_port, health_url)
    except Exception as e:
        logger.error(f"Failed to register service with Consul: {e}")
        return False