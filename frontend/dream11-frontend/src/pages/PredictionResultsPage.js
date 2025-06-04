import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';
import TeamComposition from '../components/dashboard/TeamComposition';
import PlayerTable from '../components/dashboard/PlayerTable';
import CompositionGraph from '../components/dashboard/CompositionGraph';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

const PredictionResultsPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('aggressive');
  
  // Sample data - would come from API
  const predictionData = {
    match: 'CSK vs MI',
    venue: 'Mumbai',
    pitchCondition: 'Batting Friendly',
    date: '2025-05-29',
    teams: {
      aggressive: {
        captain: 'Rohit Sharma',
        viceCaptain: 'MS Dhoni',
        players: [
          { id: 1, name: 'Rohit Sharma', team: 'MI', role: 'Batsman', points: 45, selected: 85 },
          { id: 2, name: 'MS Dhoni', team: 'CSK', role: 'Wicketkeeper', points: 40, selected: 78 },
          { id: 3, name: 'Hardik Pandya', team: 'MI', role: 'All-rounder', points: 38, selected: 72 },
          // More players would be here
        ]
      },
      balanced: {
        captain: 'Virat Kohli',
        viceCaptain: 'Jasprit Bumrah',
        players: [
          { id: 1, name: 'Virat Kohli', team: 'RCB', role: 'Batsman', points: 42, selected: 80 },
          { id: 4, name: 'Jasprit Bumrah', team: 'MI', role: 'Bowler', points: 39, selected: 74 },
          { id: 5, name: 'Ravindra Jadeja', team: 'CSK', role: 'All-rounder', points: 36, selected: 68 },
          // More players would be here
        ]
      },
      riskAverse: {
        captain: 'Jasprit Bumrah',
        viceCaptain: 'Faf du Plessis',
        players: [
          { id: 4, name: 'Jasprit Bumrah', team: 'MI', role: 'Bowler', points: 39, selected: 74 },
          { id: 6, name: 'Faf du Plessis', team: 'RCB', role: 'Batsman', points: 37, selected: 70 },
          { id: 7, name: 'Rashid Khan', team: 'GT', role: 'Bowler', points: 35, selected: 66 },
          // More players would be here
        ]
      }
    }
  };

  const tabOptions = [
    { id: 'aggressive', label: 'Aggressive' },
    { id: 'balanced', label: 'Balanced' },
    { id: 'riskAverse', label: 'Risk-Averse' }
  ];

  const handleSaveTeam = () => {
    // This would save the current team to user's saved teams
    alert('Team saved successfully!');
  };

  return (
    <MainLayout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold dark:text-white">Prediction Results</h1>
          <button 
            onClick={() => navigate('/dashboard')} 
            className="bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded focus:outline-none"
          >
            New Prediction
          </button>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Match Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Match:</span> {predictionData.match}</p>
              <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Date:</span> {predictionData.date}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Venue:</span> {predictionData.venue}</p>
              <p className="text-gray-600 dark:text-gray-400"><span className="font-medium">Pitch Condition:</span> {predictionData.pitchCondition}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 mb-6">
          <div className="mb-6">
            <nav className="flex border-b border-gray-200 dark:border-gray-700">
              {tabOptions.map((tab) => (
                <button 
                  key={tab.id} 
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-6 ${
                    activeTab === tab.id 
                      ? 'border-indigo-500 dark:border-indigo-400 border-b-2 text-indigo-600 dark:text-indigo-400' 
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                  } font-medium`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <TeamComposition 
            data={predictionData.teams[activeTab]}
            type={activeTab} 
          />

          <div className="mt-6 flex justify-end">
            <button 
              onClick={handleSaveTeam} 
              className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded focus:outline-none"
            >
              Save This Team
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Player Details</h2>
            <PlayerTable players={predictionData.teams[activeTab].players} />
          </div>
          <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Team Composition</h2>
            <CompositionGraph teamData={predictionData.teams[activeTab]} />
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default PredictionResultsPage;
