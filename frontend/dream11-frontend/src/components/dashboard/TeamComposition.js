import React from 'react';

const TeamComposition = ({ data, type }) => {
  const teamTypes = {
    aggressive: {
      description: 'High risk, high reward strategy focusing on players with high scoring potential.',
      color: 'text-red-600 dark:text-red-400'
    },
    balanced: {
      description: 'Balanced approach with a mix of consistent performers and potential high scorers.',
      color: 'text-blue-600 dark:text-blue-400'
    },
    riskAverse: {
      description: 'Conservative approach focusing on consistent performers with stable point returns.',
      color: 'text-green-600 dark:text-green-400'
    }
  };

  return (
    <div>
      <div className="mb-4">
        <h2 className={`text-xl font-bold ${teamTypes[type].color}`}>
          {type.charAt(0).toUpperCase() + type.slice(1)} Team
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">{teamTypes[type].description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="h-16 w-16 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center mr-4">
              <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-300">C</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Captain</h3>
              <p className="text-gray-700 dark:text-gray-300">{data.captain}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="h-16 w-16 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mr-4">
              <span className="text-2xl font-bold text-purple-600 dark:text-purple-300">VC</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Vice Captain</h3>
              <p className="text-gray-700 dark:text-gray-300">{data.viceCaptain}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Team Preview</h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-3">
          {data.players.map(player => (
            <div key={player.id} className="flex flex-col items-center bg-gray-50 dark:bg-gray-700 p-2 rounded-lg">
              <div className="h-12 w-12 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center mb-2">
                <span className="text-sm font-medium">{player.name.charAt(0)}</span>
              </div>
              <p className="text-xs text-center font-medium text-gray-900 dark:text-white truncate w-full">{player.name}</p>
              <p className="text-xs text-center text-gray-500 dark:text-gray-400">{player.team} | {player.role}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TeamComposition;
