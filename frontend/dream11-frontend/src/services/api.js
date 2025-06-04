import axios from 'axios';

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

// Authentication Services
export const authService = {  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login/', credentials);
      
      if (!response.data || !response.data.access || !response.data.refresh) {
        console.error('Invalid response format from login endpoint:', response);
        throw new Error('Invalid response from authentication server');
      }
      
      const { access, refresh } = response.data;
      
      // Store tokens (let the AuthContext handle this instead)
      // This is now redundant as AuthContext.login will handle saving tokens
      // But keeping it for safety
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      return response.data;
    } catch (error) {
      console.error('Login API error:', error.response || error);
      throw error;
    }
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/users/me/');
    return response.data;
  },
    refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    // Use our api instance with interceptors, not raw axios
    const response = await api.post(`/auth/token/refresh/`, {
      refresh: refreshToken
    }, {
      // Skip the auth interceptor for this specific request
      skipAuthRefresh: true
    });
    
    const { access } = response.data;
    localStorage.setItem('access_token', access);
    
    return access;
  }
};

// Team and Venue Services
export const teamService = {
  getAllTeams: async () => {
    const response = await api.get('/teams/');
    return response.data;
  },
  
  getTeamById: async (teamId) => {
    const response = await api.get(`/teams/${teamId}/`);
    return response.data;
  },
  
  getTeamPlayers: async (teamId) => {
    const response = await api.get(`/teams/${teamId}/players/`);
    return response.data;
  }
};

export const venueService = {
  getAllVenues: async () => {
    const response = await api.get('/venues/');
    return response.data;
  },
  
  getVenueById: async (venueId) => {
    const response = await api.get(`/venues/${venueId}/`);
    return response.data;
  }
};

// Prediction Service
export const predictionService = {
  predictTeam: async (data) => {
    const response = await api.post('/predict_team_with_pipeline/', {
      team1: data.team1,
      team2: data.team2,
      venue: data.venue,
      pitch_type: data.pitchCondition,
      update_data: data.updateData || false
    });
    return response.data;
  },
  
  updatePlayerData: async () => {
    const response = await api.post('/update_player_data/');
    return response.data;
  },
  
  checkPipelineStatus: async () => {
    const response = await api.get('/check_pipeline_status/');
    return response.data;
  },
  
  getUserHistory: async () => {
    const response = await api.get('/predictions/history/');
    return response.data;
  },
  
  getPredictionById: async (id) => {
    const response = await api.get(`/predictions/${id}/`);
    return response.data;
  },
  
  likePrediction: async (id, isLike = true) => {
    const response = await api.post(`/predictions/${id}/like/`, { is_like: isLike });
    return response.data;
  }
};

// Player Service
export const playerService = {
  getAllPlayers: async () => {
    const response = await api.get('/players/');
    return response.data;
  },
  
  getPlayerById: async (playerId) => {
    const response = await api.get(`/players/${playerId}/`);
    return response.data;
  },
  
  getPlayerStats: async (playerId) => {
    const response = await api.get(`/players/${playerId}/stats/`);
    return response.data;
  },
  
  addComment: async (playerId, comment) => {
    const response = await api.post(`/players/${playerId}/comments/`, { comment });
    return response.data;
  }
};

// Export default API instance
export default api;
