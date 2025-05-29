import React from 'react';
import { useTheme } from '../../context/ThemeContext';

const PlayerTable = ({ players, title, type }) => {
  const { darkMode } = useTheme();
  
  // Function to determine the color for different prediction types
  const getPredictionTypeColor = (type) => {
    switch(type) {
      case 'AGG':
        return 'text-red-600 dark:text-red-400';
      case 'BAL':
        return 'text-blue-600 dark:text-blue-400';
      case 'RISK':
        return 'text-green-600 dark:text-green-400';
      default:
        return '';
    }
  };
  
  return (
    <div className="w-full mb-8">
      <h2 className={`text-xl font-bold mb-4 ${getPredictionTypeColor(type)}`}>{title}</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white dark:bg-gray-800 rounded-lg overflow-hidden">
          <thead className="bg-gray-100 dark:bg-gray-700">
            <tr>
              <th className="py-2 px-4 text-left text-sm font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">Role</th>
              <th className="py-2 px-4 text-left text-sm font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">Player</th>
              <th className="py-2 px-4 text-left text-sm font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">Team</th>
              <th className="py-2 px-4 text-left text-sm font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">Points</th>
              <th className="py-2 px-4 text-left text-sm font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">Captain</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
            {players.map((player, idx) => (
              <tr key={idx} className={`${idx % 2 === 0 ? 'bg-gray-50 dark:bg-gray-900/30' : ''} hover:bg-gray-100 dark:hover:bg-gray-700`}>
                <td className="py-3 px-4 text-sm text-gray-800 dark:text-gray-200">
                  {player.role === 'BAT' && 'Batsman'}
                  {player.role === 'BWL' && 'Bowler'}
                  {player.role === 'AR' && 'All-Rounder'}
                  {player.role === 'WK' && 'Wicket-Keeper'}
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center">
                    <div className="ml-2">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{player.name}</div>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4 text-sm text-gray-800 dark:text-gray-200">{player.team}</td>
                <td className="py-3 px-4 text-sm text-gray-800 dark:text-gray-200">{player.points}</td>
                <td className="py-3 px-4">
                  {player.is_captain && (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100">
                      C
                    </span>
                  )}
                  {player.is_vice_captain && (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100">
                      VC
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PlayerTable;
