import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ApiTest = () => {
  const [status, setStatus] = useState('idle');
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

  const API_URL = 'http://localhost:8000/api';
  
  const testLogin = async () => {
    try {
      setStatus('loading');
      const response = await axios.post(`${API_URL}/login/`, {
        username: 'testuser123',
        password: 'Test@123456'
      });
      
      if (response.data && response.data.access) {
        localStorage.setItem('token', response.data.access);
        return response.data.access;
      }
      throw new Error('No access token received');
    } catch (err) {
      throw err;
    }
  };

  const fetchData = async (token) => {
    try {
      const teamsResponse = await axios.get(`${API_URL}/teams/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const venuesResponse = await axios.get(`${API_URL}/venues/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const playersResponse = await axios.get(`${API_URL}/players/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      return {
        teams: teamsResponse.data,
        venues: venuesResponse.data,
        players: playersResponse.data.slice(0, 5) // Just get the first 5 players
      };
    } catch (err) {
      throw err;
    }
  };

  const runTests = async () => {
    try {
      setStatus('loading');
      setError(null);
      
      // Step 1: Login
      const token = await testLogin();
      console.log('Login successful, token:', token.substring(0, 15) + '...');
      
      // Step 2: Fetch data
      const data = await fetchData(token);
      console.log('Data fetched successfully:', data);
      
      // Step 3: Make a prediction if we have teams and venues
      if (data.teams.length >= 2 && data.venues.length >= 1) {
        const predictionResponse = await axios.post(
          `${API_URL}/predict-team/`,
          {
            team1: data.teams[0].id,
            team2: data.teams[1].id,
            venue: data.venues[0].id,
            pitch_type: 'BAL'
          },
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        
        console.log('Prediction successful:', predictionResponse.data);
        
        // Set results
        setResults({
          login: 'Success',
          teams: data.teams.length,
          venues: data.venues.length,
          players: data.players.length,
          prediction: 'Success',
          predictionTypes: Object.keys(predictionResponse.data.predictions)
        });
      } else {
        setResults({
          login: 'Success',
          teams: data.teams.length,
          venues: data.venues.length,
          players: data.players.length,
          prediction: 'Failed - Not enough teams or venues'
        });
      }
      
      setStatus('success');
    } catch (err) {
      console.error('Test failed:', err);
      setError(err.message || 'Unknown error occurred');
      setStatus('error');
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">API Connection Test</h1>
      
      <button
        onClick={runTests}
        disabled={status === 'loading'}
        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 mb-4"
      >
        {status === 'loading' ? 'Testing...' : 'Run API Tests'}
      </button>
      
      {status === 'error' && (
        <div className="p-4 mb-4 bg-red-100 text-red-700 border-l-4 border-red-500 dark:bg-red-900/30 dark:text-red-300">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}
      
      {status === 'success' && (
        <div className="p-4 mb-4 bg-green-100 text-green-700 border-l-4 border-green-500 dark:bg-green-900/30 dark:text-green-300">
          <p className="font-bold">Success! Backend API is working properly.</p>
        </div>
      )}
      
      {status === 'success' && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold mb-2 text-gray-800 dark:text-white">Results</h2>
          <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
            <p><strong>Login:</strong> {results.login}</p>
            <p><strong>Teams Fetched:</strong> {results.teams}</p>
            <p><strong>Venues Fetched:</strong> {results.venues}</p>
            <p><strong>Players Fetched:</strong> {results.players}</p>
            <p><strong>Prediction:</strong> {results.prediction}</p>
            {results.predictionTypes && (
              <p><strong>Prediction Types:</strong> {results.predictionTypes.join(', ')}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiTest;
