import { api } from './api';

export const predictionService = {
  // Get all teams
  getTeams: async () => {
    try {
      const response = await api.get('/teams/');
      return response.data;
    } catch (error) {
      console.error('Error fetching teams:', error);
      throw error;
    }
  },
  
  // Get players for a specific team
  getTeamPlayers: async (teamId) => {
    try {
      const response = await api.get(`/teams/${teamId}/players/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching team players:', error);
      throw error;
    }
  },
  
  // Load data from CSV files
  loadCsvData: async () => {
    try {
      const response = await api.post('/load-csv-data/');
      return response.data;
    } catch (error) {
      console.error('Error loading CSV data:', error);
      throw error;
    }
  },
  
  // Generate team prediction
  predictTeam: async (team1, team2, budget = 100) => {
    try {
      const response = await api.post('/predict-team/', {
        team1,
        team2,
        budget
      });
      return response.data;
    } catch (error) {
      console.error('Error predicting team:', error);
      throw error;
    }
  },
  
  // Get user predictions
  getUserPredictions: async () => {
    try {
      const response = await api.get('/predictions/');
      return response.data;
    } catch (error) {
      console.error('Error fetching predictions:', error);
      throw error;
    }
  },
  
  // Get prediction details
  getPredictionDetails: async (predictionId) => {
    try {
      const response = await api.get(`/predictions/${predictionId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching prediction details:', error);
      throw error;
    }
  },
// Get player details
  getPlayerDetails: async (playerId) => {
    try {
      // Assuming the endpoint is /players/{playerId}/ or similar, adjust if needed
      const response = await api.get(`/players/${playerId}/details/`); // Or just /players/${playerId}/ if that's the detail view
      return response.data;
    } catch (error) {
      console.error('Error fetching player details:', error);
      throw error;
    }
  },
};

export default predictionService;
