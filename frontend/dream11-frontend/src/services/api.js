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
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication Services
export const authService = {
  login: async (credentials) => {
    const response = await api.post('/login', credentials);
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/register', userData);
    return response.data;
  },
  
  getUserProfile: async () => {
    const response = await api.get('/user/profile');
    return response.data;
  }
};

// Prediction Services
export const predictionService = {
  predictTeam: async (data) => {
    const response = await api.post('/predict-team', data);
    return response.data;
  },
  
  getUserHistory: async () => {
    const response = await api.get('/user/history');
    return response.data;
  },
  
  likeTeam: async (predictionId) => {
    const response = await api.post(`/team/like`, { predictionId });
    return response.data;
  },
  
  dislikeTeam: async (predictionId) => {
    const response = await api.post(`/team/dislike`, { predictionId });
    return response.data;
  },
  
  commentOnTeam: async (predictionId, comment) => {
    const response = await api.post(`/team/comment`, { predictionId, comment });
    return response.data;
  }
};

// Player Services
export const playerService = {
  getPlayerDetails: async (playerId) => {
    const response = await api.get(`/player/${playerId}`);
    return response.data;
  }
};

export default {
  authService,
  predictionService,
  playerService
};
