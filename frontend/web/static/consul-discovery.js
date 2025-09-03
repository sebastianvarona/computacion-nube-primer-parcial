/**
 * Consul Service Discovery Utility for Frontend
 * Provides dynamic service URL discovery for microservices
 */

class ServiceDiscovery {
    constructor() {
        this.serviceCache = {};
        this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Get service URL from Consul via frontend API
     * @param {string} serviceName - Name of the service (microusers, microproducts, microorders)
     * @returns {Promise<string>} - Service URL
     */
    async getServiceUrl(serviceName) {
        // Check cache first
        const cached = this.serviceCache[serviceName];
        if (cached && (Date.now() - cached.timestamp) < this.cacheExpiry) {
            return cached.url;
        }

        try {
            const response = await fetch(`/api/services/${serviceName}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Cache the result
                this.serviceCache[serviceName] = {
                    url: data.url,
                    timestamp: Date.now()
                };
                return data.url;
            } else {
                throw new Error(data.message || `Service ${serviceName} not found`);
            }
        } catch (error) {
            console.error(`Failed to discover service ${serviceName}:`, error);
            // Fallback to hardcoded URLs as last resort
            return this.getFallbackUrl(serviceName);
        }
    }

    /**
     * Get all available services
     * @returns {Promise<Object>} - Object with service names as keys and URLs as values
     */
    async getAllServices() {
        try {
            const response = await fetch('/api/services');
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update cache
                const timestamp = Date.now();
                Object.entries(data.services).forEach(([serviceName, url]) => {
                    this.serviceCache[serviceName] = { url, timestamp };
                });
                return data.services;
            } else {
                throw new Error(data.message || 'Failed to get services');
            }
        } catch (error) {
            console.error('Failed to get all services:', error);
            return {};
        }
    }

    /**
     * Fallback URLs in case Consul is not available
     * @param {string} serviceName - Service name
     * @returns {string} - Fallback URL
     */
    getFallbackUrl(serviceName) {
        const fallbacks = {
            'microusers': 'http://192.168.80.3:5002',
            'microproducts': 'http://192.168.80.3:5003',
            'microorders': 'http://192.168.80.3:5004'
        };
        
        console.warn(`Using fallback URL for ${serviceName}`);
        return fallbacks[serviceName] || '';
    }

    /**
     * Build API URL for a service endpoint
     * @param {string} serviceName - Service name
     * @param {string} endpoint - API endpoint (e.g., '/api/users')
     * @returns {Promise<string>} - Complete API URL
     */
    async buildApiUrl(serviceName, endpoint) {
        const baseUrl = await this.getServiceUrl(serviceName);
        return `${baseUrl}${endpoint}`;
    }

    /**
     * Clear service cache
     */
    clearCache() {
        this.serviceCache = {};
    }
}

// Global instance
const serviceDiscovery = new ServiceDiscovery();

// Convenience functions for common services
window.getServiceUrl = (serviceName) => serviceDiscovery.getServiceUrl(serviceName);
window.buildApiUrl = (serviceName, endpoint) => serviceDiscovery.buildApiUrl(serviceName, endpoint);
window.getAllServices = () => serviceDiscovery.getAllServices();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ServiceDiscovery;
}