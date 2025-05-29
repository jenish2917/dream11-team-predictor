import React, { useState } from 'react';
import { useTheme } from '../../context/ThemeContext';
import PlayerTable from './PlayerTable';

const PredictionResults = ({ predictions, graphs }) => {
  const { darkMode } = useTheme();
  const [activeTab, setActiveTab] = useState('aggressive');
  
  // Check if predictions exist
  if (!predictions || !predictions.AGG || !predictions.BAL || !predictions.RISK) {
    return (
      <div className="text-center p-10">
        <p className="text-gray-700 dark:text-gray-300">No prediction data available.</p>
      </div>
    );
  }

  // Extract players from predictions
  const getPlayersFromPrediction = (prediction) => {
    if (!prediction || !prediction.players) return [];
    
    return prediction.players.map(item => ({
      id: item.player.id,
      name: item.player.name,
      team: item.player.team.short_name,
      role: item.player.role,
      points: item.expected_points,
      is_captain: item.is_captain,
      is_vice_captain: item.is_vice_captain
    }));
  };
  
  const aggressivePlayers = getPlayersFromPrediction(predictions.AGG);
  const balancedPlayers = getPlayersFromPrediction(predictions.BAL);
  const riskAversePlayers = getPlayersFromPrediction(predictions.RISK);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
      <h2 className="text-2xl font-bold mb-6 text-gray-800 dark:text-white">Prediction Results</h2>
      
      {/* Team Selection Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
        <button
          onClick={() => setActiveTab('aggressive')}
          className={`py-2 px-4 text-sm font-medium ${
            activeTab === 'aggressive'
              ? 'text-red-600 dark:text-red-400 border-b-2 border-red-600 dark:border-red-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          Aggressive Team
        </button>
        <button
          onClick={() => setActiveTab('balanced')}
          className={`py-2 px-4 text-sm font-medium ${
            activeTab === 'balanced'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          Balanced Team
        </button>
        <button
          onClick={() => setActiveTab('risk-averse')}
          className={`py-2 px-4 text-sm font-medium ${
            activeTab === 'risk-averse'
              ? 'text-green-600 dark:text-green-400 border-b-2 border-green-600 dark:border-green-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          Risk-Averse Team
        </button>
      </div>
      
      {/* Display the selected team */}
      <div className="mt-4">
        {activeTab === 'aggressive' && (
          <PlayerTable
            players={aggressivePlayers}
            title="Aggressive Strategy Team"
            type="AGG"
          />
        )}
        
        {activeTab === 'balanced' && (
          <PlayerTable
            players={balancedPlayers}
            title="Balanced Strategy Team"
            type="BAL"
          />
        )}
        
        {activeTab === 'risk-averse' && (
          <PlayerTable
            players={riskAversePlayers}
            title="Risk-Averse Strategy Team"
            type="RISK"
          />
        )}
      </div>
      
      {/* Team Composition Graph */}
      {graphs && graphs.composition && (
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Team Composition</h3>
          <div className="bg-white dark:bg-gray-900 p-4 rounded-lg">
            <img 
              src={`data:image/png;base64,${graphs.composition}`} 
              alt="Team Composition" 
              className="w-full h-auto"
            />
          </div>
        </div>
      )}
      
      {/* Performance Analysis */}
      {graphs && graphs.performance && (
        <div className="mt-8">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Performance Analysis</h3>
          <div className="bg-white dark:bg-gray-900 p-4 rounded-lg">
            <img 
              src={`data:image/png;base64,${graphs.performance}`} 
              alt="Performance Analysis" 
              className="w-full h-auto"
            />
          </div>
        </div>
      )}
      
      {/* Social Interaction */}
      <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            <button className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"></path>
              </svg>
              <span>Like</span>
            </button>
            <button className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2"></path>
              </svg>
              <span>Dislike</span>
            </button>
          </div>
          <button className="text-blue-600 dark:text-blue-400 hover:underline">
            Save to History
          </button>
        </div>
      </div>
    </div>
  );
};

export default PredictionResults;
