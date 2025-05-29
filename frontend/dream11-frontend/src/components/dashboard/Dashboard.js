import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import PredictionResults from '../prediction/PredictionResults';

const PredictionForm = () => {
  const [formData, setFormData] = useState({
    team1: '',
    team2: '',
    venue: '',
    pitchType: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Example data - in a real application, these would come from the backend
  const iplTeams = [
    'Chennai Super Kings',
    'Mumbai Indians',
    'Royal Challengers Bangalore',
    'Delhi Capitals',
    'Kolkata Knight Riders',
    'Punjab Kings',
    'Rajasthan Royals',
    'Sunrisers Hyderabad',
    'Gujarat Titans',
    'Lucknow Super Giants'
  ];
  
  const venues = [
    'M. A. Chidambaram Stadium, Chennai',
    'Wankhede Stadium, Mumbai',
    'M. Chinnaswamy Stadium, Bangalore',
    'Arun Jaitley Stadium, Delhi',
    'Eden Gardens, Kolkata',
    'IS Bindra Stadium, Mohali',
    'Sawai Mansingh Stadium, Jaipur',
    'Rajiv Gandhi International Cricket Stadium, Hyderabad',
    'Narendra Modi Stadium, Ahmedabad',
    'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow'
  ];
  
  const pitchTypes = [
    'Batting-friendly',
    'Bowling-friendly',
    'Balanced',
    'Spin-friendly',
    'Pace-friendly',
    'Dry',
    'Damp'
  ];
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      // In a real application, this would call the API
      // const response = await predictionService.predictTeam(formData);
      // Handle success
      console.log('Prediction form submitted:', formData);
      // Redirect to results page or show results
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to generate prediction. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4">Generate Prediction</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="team1" className="block text-sm font-medium text-gray-700 mb-1">Team 1</label>
            <select
              id="team1"
              name="team1"
              value={formData.team1}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-green-500 focus:border-green-500"
            >
              <option value="">Select Team 1</option>
              {iplTeams.map((team) => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="team2" className="block text-sm font-medium text-gray-700 mb-1">Team 2</label>
            <select
              id="team2"
              name="team2"
              value={formData.team2}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-green-500 focus:border-green-500"
              disabled={!formData.team1}
            >
              <option value="">Select Team 2</option>
              {iplTeams
                .filter((team) => team !== formData.team1)
                .map((team) => (
                  <option key={team} value={team}>{team}</option>
                ))
              }
            </select>
          </div>
          
          <div>
            <label htmlFor="venue" className="block text-sm font-medium text-gray-700 mb-1">Venue</label>
            <select
              id="venue"
              name="venue"
              value={formData.venue}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-green-500 focus:border-green-500"
            >
              <option value="">Select Venue</option>
              {venues.map((venue) => (
                <option key={venue} value={venue}>{venue}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="pitchType" className="block text-sm font-medium text-gray-700 mb-1">Pitch Type</label>
            <select
              id="pitchType"
              name="pitchType"
              value={formData.pitchType}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-green-500 focus:border-green-500"
            >
              <option value="">Select Pitch Type</option>
              {pitchTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="mt-6">
          <button
            type="submit"
            disabled={isLoading || !formData.team1 || !formData.team2 || !formData.venue || !formData.pitchType}
            className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 
              ${(isLoading || !formData.team1 || !formData.team2 || !formData.venue || !formData.pitchType) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? 'Generating Prediction...' : 'Generate Prediction'}
          </button>
        </div>
      </form>
    </div>
  );
};

const Dashboard = () => {
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Dream11 Team Predictor</h1>
      <PredictionForm />
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4">Recent Predictions</h2>
        <p className="text-gray-500">Your recent prediction results will appear here.</p>
      </div>
    </div>
  );
};

export default Dashboard;
