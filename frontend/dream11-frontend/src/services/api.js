import axios from 'axios';
import { authService } from './authService'; // Import standalone authService

// Base URL for API calls
const API_BASE_URL = 'http://localhost:8000/api'; // This will be replaced with actual backend URL

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add a request interceptor to inject token into headers
api.interceptors.request.use(
  (config) => {
    // Skip adding auth headers for token refresh calls
    if (config.skipAuthRefresh) {
      return config;
    }
    
    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    
    // Only attach token if it exists
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  // Clear the queue
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized errors that might be due to expired token
    if (error.response?.status === 401 && !originalRequest._retry) {
      // If already refreshing, add request to queue
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
        try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        // If no refresh token exists, logout
        if (!refreshToken) {
          // Redirect to login
          window.location.href = '/login';
          return Promise.reject(new Error('No refresh token available'));
        }
        
        // Use the refreshToken method that we fixed
        const newAccessToken = await authService.refreshToken();
        
        // Update original request with new token
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        
        // Process any queued requests
        processQueue(null, newAccessToken);
        
        return api(originalRequest);
      } catch (refreshError) {
        // Process queued requests with error
        processQueue(refreshError, null);
        
        // Clear tokens on refresh failure - user needs to login again
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    // For errors other than 401, just reject
    return Promise.reject(error);
  }
);

// NOTE: Service definitions (authService, teamService, venueService, predictionService, playerService)
// have been moved to their own respective files (e.g., authService.js, predictionService.js).
// This api.js file now only contains the core axios instance and its interceptors.

// Export default API instance
export default api;
