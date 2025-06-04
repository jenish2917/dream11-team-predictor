import axios from 'axios';

// API service for dream11 team prediction
const API_URL = 'http://localhost:8000/api';

// Set auth token for API requests
const setAuthToken = (token) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

// Check and set token from localStorage if available
const initializeAuthToken = () => {
  const token = localStorage.getItem('access_token');
  if (token) {
    setAuthToken(token);
  }
};

// Initialize auth token on module load
initializeAuthToken();

// Get all teams
export const getAllTeams = async () => {
  try {
    const response = await axios.get(`${API_URL}/predictor/teams/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching teams:', error);
    throw error;
  }
};

// Get players for a team
export const getTeamPlayers = async (team) => {
  try {
    const response = await axios.get(`${API_URL}/predictor/team_players/`, {
      params: { team }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching team players:', error);
    throw error;
  }
};

// Predict dream11 team
export const predictTeam = async (team1, team2, budget = 100, teamSize = 11) => {
  try {
    const response = await axios.post(`${API_URL}/predictor/predict_team/`, {
      team1,
      team2,
      budget,
      team_size: teamSize
    });
    return response.data;
  } catch (error) {
    console.error('Error predicting team:', error);
    throw error;
  }
};

// Get player details
export const getPlayerDetails = async (player) => {
  try {
    const response = await axios.get(`${API_URL}/predictor/player_details/`, {
      params: { player }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching player details:', error);
    throw error;
  }
};

export default {
  setAuthToken,
  getAllTeams,
  getTeamPlayers,
  predictTeam,
  getPlayerDetails
};
