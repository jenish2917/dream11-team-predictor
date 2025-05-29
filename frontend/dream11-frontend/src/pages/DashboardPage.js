import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    team1: '',
    team2: '',
    venue: '',
    pitchCondition: '',
    date: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Sample data for form fields
  const teams = ['Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bangalore', 
                'Kolkata Knight Riders', 'Delhi Capitals', 'Rajasthan Royals', 
                'Sunrisers Hyderabad', 'Punjab Kings', 'Gujarat Titans', 'Lucknow Super Giants'];

  const venues = ['Mumbai - Wankhede Stadium', 'Chennai - M.A. Chidambaram Stadium', 
                'Bangalore - M. Chinnaswamy Stadium', 'Kolkata - Eden Gardens', 
                'Delhi - Arun Jaitley Stadium', 'Ahmedabad - Narendra Modi Stadium',
                'Hyderabad - Rajiv Gandhi International Stadium', 'Mohali - IS Bindra Stadium',
                'Jaipur - Sawai Mansingh Stadium', 'Lucknow - BRSABV Ekana Cricket Stadium'];

  const pitchConditions = ['Batting Friendly', 'Bowling Friendly', 'Balanced', 'Spin Friendly', 'Pace Friendly', 'Used Pitch'];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const validateForm = () => {
    if (!formData.team1) return 'Team 1 is required';
    if (!formData.team2) return 'Team 2 is required';
    if (formData.team1 === formData.team2) return 'Teams cannot be the same';
    if (!formData.venue) return 'Venue is required';
    if (!formData.pitchCondition) return 'Pitch condition is required';
    if (!formData.date) return 'Match date is required';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errorMsg = validateForm();
    if (errorMsg) {
      setError(errorMsg);
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      // For demo purposes, we'll simulate an API call
      // In a real app, you would make an API call to generate predictions
      // const response = await api.predictions.generate(formData);
      
      // Simulate API delay
      setTimeout(() => {
        setLoading(false);
        // Navigate to prediction results page
        navigate('/prediction-results');
      }, 2000);
    } catch (err) {
      console.error("Error generating prediction:", err);
      setError('Failed to generate prediction. Please try again.');
      setLoading(false);
    }
  };

  const recentMatches = [
    { id: 1, team1: 'MI', team2: 'CSK', venue: 'Mumbai', date: '2025-05-25' },
    { id: 2, team1: 'RCB', team2: 'KKR', venue: 'Bangalore', date: '2025-05-24' },
    { id: 3, team1: 'SRH', team2: 'PBKS', venue: 'Hyderabad', date: '2025-05-22' }
  ];

  return (
    <MainLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6 dark:text-white">Dream11 Team Predictor</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prediction Form */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">Predict Your Winning Team</h2>
              
              {error && (
                <div className="mb-4 bg-red-100 border border-red-400 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200 px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
              
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="team1" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Team 1
                    </label>
                    <select
                      id="team1"
                      name="team1"
                      value={formData.team1}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Select Team 1</option>
                      {teams.map(team => (
                        <option key={team} value={team}>{team}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="team2" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Team 2
                    </label>
                    <select
                      id="team2"
                      name="team2"
                      value={formData.team2}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Select Team 2</option>
                      {teams.map(team => (
                        <option key={team} value={team} disabled={team === formData.team1}>{team}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="venue" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Venue
                    </label>
                    <select
                      id="venue"
                      name="venue"
                      value={formData.venue}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Select Venue</option>
                      {venues.map(venue => (
                        <option key={venue} value={venue}>{venue}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="pitchCondition" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Pitch Condition
                    </label>
                    <select
                      id="pitchCondition"
                      name="pitchCondition"
                      value={formData.pitchCondition}
                      onChange={handleChange}
                      className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Select Pitch Condition</option>
                      {pitchConditions.map(condition => (
                        <option key={condition} value={condition}>{condition}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="mb-6">
                  <label htmlFor="date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Match Date
                  </label>
                  <input
                    type="date"
                    id="date"
                    name="date"
                    value={formData.date}
                    onChange={handleChange}
                    min={new Date().toISOString().split('T')[0]}
                    className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                      loading ? 'opacity-70 cursor-not-allowed' : ''
                    }`}
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating Predictions...
                      </>
                    ) : (
                      'Generate Predictions'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
          
          {/* Recent Matches */}
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">Recent Matches</h2>
              
              <div className="space-y-4">
                {recentMatches.map(match => (
                  <div key={match.id} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{match.team1} vs {match.team2}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{match.venue} • {match.date}</p>
                      </div>
                      <button 
                        className="text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                        onClick={() => navigate('/prediction-results')}
                      >
                        View
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4">
                <button 
                  onClick={() => navigate('/history')} 
                  className="text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 hover:underline"
                >
                  View All Past Predictions →
                </button>
              </div>
            </div>
            
            {/* Tips Card */}
            <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">Pro Tips</h2>
              
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  <span>Consider the head-to-head history between teams.</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  <span>Include players who perform well at specific venues.</span>
                </li>
                <li className="flex items-start">
                  <svg className="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  <span>Balance your team with both high-risk and consistent performers.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default DashboardPage;
