import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import { getAllTeams, predictTeam } from '../services/predictorService';

const PredictionPage = () => {
  const navigate = useNavigate();
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [form, setForm] = useState({
    team1: null,
    team2: null,
    budget: 100,
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch all teams when component mounts
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const teamsData = await getAllTeams();
        const teamOptions = teamsData.map(team => ({ value: team, label: team }));
        setTeams(teamOptions);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch teams. Please try again later.');
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!form.team1 || !form.team2) {
      setError('Please select both teams');
      return;
    }
    
    if (form.team1.value === form.team2.value) {
      setError('Please select different teams');
      return;
    }
    
    try {
      setPredicting(true);
      setError(null);
      
      // Call API to predict team
      const result = await predictTeam(
        form.team1.value,
        form.team2.value,
        form.budget
      );
      
      // Navigate to results page with prediction data
      navigate('/prediction-results', { state: { prediction: result } });
    } catch (err) {
      setError('Failed to predict team. Please try again later.');
      setPredicting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Predict Dream11 Team</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 mb-2">Team 1</label>
          <Select
            options={teams}
            value={form.team1}
            onChange={(selected) => setForm({...form, team1: selected})}
            isLoading={loading}
            isDisabled={loading || predicting}
            placeholder="Select first team"
            className="text-gray-700"
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 mb-2">Team 2</label>
          <Select
            options={teams}
            value={form.team2}
            onChange={(selected) => setForm({...form, team2: selected})}
            isLoading={loading}
            isDisabled={loading || predicting}
            placeholder="Select second team"
            className="text-gray-700"
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-700 mb-2">
            Budget (in credits): {form.budget}
          </label>
          <input
            type="range"
            min="80"
            max="120"
            step="1"
            value={form.budget}
            onChange={(e) => setForm({...form, budget: parseInt(e.target.value)})}
            disabled={predicting}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>80</span>
            <span>100</span>
            <span>120</span>
          </div>
        </div>
        
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={loading || predicting || !form.team1 || !form.team2}
            className={`px-6 py-2 rounded-md text-white font-medium ${
              loading || predicting || !form.team1 || !form.team2
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {predicting ? 'Predicting...' : 'Predict Dream11 Team'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PredictionPage;
