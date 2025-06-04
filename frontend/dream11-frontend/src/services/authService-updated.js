// Authentication API service
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Auth Service Object
export const authService = {  // Login user
  login: async (credentials) => {
    try {
      const response = await axios.post(`${API_URL}/login/`, credentials);
      
      if (response.data.access) {
        // Store JWT tokens in localStorage
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        console.log("Login successful, tokens stored");
      } else {
        console.error("Login response missing tokens:", response.data);
      }
      
      return response.data;
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
      throw error;
    }
  },
    // Register new user
  register: async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/register/`, userData);
      
      if (response.data.access) {
        // Store JWT tokens in localStorage
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        console.log("Registration successful, tokens stored");
      }
      
      return response.data;
    } catch (error) {
      console.error("Registration failed:", error.response?.data || error.message);
      throw error;
    }
  },
    // Refresh access token using refresh token
  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        throw new Error("No refresh token available");
      }
      
      const response = await axios.post(
        `${API_URL}/token/refresh/`, 
        { refresh: refreshToken },
        { skipAuthRefresh: true } // Skip auth interceptor for this call
      );
      
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        return response.data.access;
      }
      
      return null;
    } catch (error) {
      console.error("Token refresh failed:", error);
      // Clear tokens if refresh fails
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return null;
    }
  },
  
  // Logout user
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  }
};

export default authService;
