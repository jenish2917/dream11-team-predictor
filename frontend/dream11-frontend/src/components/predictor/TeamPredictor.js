import React, { useState, useEffect } from 'react';
import predictionService from '../../services/predictionService';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const TeamPredictor = () => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState('');
  const [prediction, setPrediction] = useState(null);
  
  const [formData, setFormData] = useState({
    team1: '',
    team2: '',
    budget: 100,
  });

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const teamsData = await predictionService.getTeams();
        setTeams(teamsData);
      } catch (err) {
        setError('Failed to load teams. Please make sure you have loaded data from CSV files.');
        console.error('Error loading teams:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setPredicting(true);
      setError('');
      setPrediction(null);
      
      const result = await predictionService.predictTeam(formData.team1, formData.team2, formData.budget);
      setPrediction(result.prediction);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate prediction');
      console.error('Error predicting team:', err);
    } finally {
      setPredicting(false);
    }
  };

  const renderPlayerCard = (player, index) => {
    const isCaptain = player.is_captain;
    const isViceCaptain = player.is_vice_captain;
    
    return (
      <div key={index} className="bg-white rounded-lg shadow-md p-4 flex flex-col items-center justify-center">
        <div className="font-bold text-lg mb-2">
          {player.name} 
          {isCaptain && <span className="ml-1 text-green-600">(C)</span>}
          {isViceCaptain && <span className="ml-1 text-blue-600">(VC)</span>}
        </div>
        
        <div className="text-sm text-gray-600 mb-1">{player.role}</div>
        <div className="text-sm text-gray-600 mb-1">{player.team}</div>
        
        <div className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full mt-2">
          {player.fantasy_points ? player.fantasy_points.toFixed(1) : '0'} pts
        </div>
      </div>
    );
  };

  const renderTeamComposition = () => {
    if (!prediction || !prediction.team) return null;

    // Group players by role
    const wicketKeepers = prediction.team.filter(p => p.role === 'Wicket-Keeper');
    const batsmen = prediction.team.filter(p => p.role === 'Batsman');
    const allRounders = prediction.team.filter(p => p.role === 'All-Rounder');
    const bowlers = prediction.team.filter(p => p.role === 'Bowler');

    return (
      <div className="mt-8">
        <h3 className="text-xl font-bold mb-4">Predicted Team</h3>
        
        {/* Wicket Keepers */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-2 text-blue-700">Wicket Keepers ({wicketKeepers.length})</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {wicketKeepers.map(renderPlayerCard)}
          </div>
        </div>
        
        {/* Batsmen */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-2 text-green-700">Batsmen ({batsmen.length})</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {batsmen.map(renderPlayerCard)}
          </div>
        </div>
        
        {/* All Rounders */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-2 text-purple-700">All Rounders ({allRounders.length})</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {allRounders.map(renderPlayerCard)}
          </div>
        </div>
        
        {/* Bowlers */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold mb-2 text-red-700">Bowlers ({bowlers.length})</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {bowlers.map(renderPlayerCard)}
          </div>
        </div>
        
        {/* Team Summary */}
        <div className="bg-gray-100 p-4 rounded-lg mt-4">
          <h4 className="font-bold mb-2">Team Summary</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p>Total Score: {prediction.score?.toFixed(1) || '0'}</p>
              <p>Budget Used: {prediction.budget_used?.toFixed(1) || '0'} cr</p>
              <p>Budget Remaining: {prediction.budget_remaining?.toFixed(1) || '0'} cr</p>
            </div>
            <div>
              <p>WK: {prediction.roles?.['Wicket-Keeper'] || 0}</p>
              <p>BAT: {prediction.roles?.['Batsman'] || 0}</p>
              <p>AR: {prediction.roles?.['All-Rounder'] || 0}</p>
              <p>BOWL: {prediction.roles?.['Bowler'] || 0}</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Dream11 Team Predictor</h2>
      
      {/* Prediction Form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="team1">
              Team 1
            </label>
            <select
              id="team1"
              name="team1"
              value={formData.team1}
              onChange={handleChange}
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              disabled={loading}
            >
              <option value="">Select Team 1</option>
              {teams.map((team) => (
                <option key={`team1-${team.id}`} value={team.name || team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="team2">
              Team 2
            </label>
            <select
              id="team2"
              name="team2"
              value={formData.team2}
              onChange={handleChange}
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              disabled={loading}
            >
              <option value="">Select Team 2</option>
              {teams.map((team) => (
                <option key={`team2-${team.id}`} value={team.name || team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="budget">
              Budget (in Crores)
            </label>
            <input
              id="budget"
              name="budget"
              type="number"
              min="50"
              max="200"
              value={formData.budget}
              onChange={handleChange}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              disabled={loading}
            />
          </div>
        </div>
        
        <div className="flex items-center justify-center mt-4">
          <button
            type="submit"
            disabled={predicting || loading}
            className={`bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded focus:outline-none focus:shadow-outline ${
              predicting || loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {predicting ? 'Predicting...' : 'Predict Best Team'}
          </button>
        </div>
      </form>
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6" role="alert">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}
      
      {/* Render prediction results */}
      {prediction && renderTeamComposition()}
    </div>
  );
};

export default TeamPredictor;
