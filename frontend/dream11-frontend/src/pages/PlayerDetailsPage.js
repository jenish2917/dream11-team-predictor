import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getPlayerDetails } from '../services/predictorService';

const PlayerDetailsPage = () => {
  const { playerName } = useParams();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlayerDetails = async () => {
      try {
        setLoading(true);
        const details = await getPlayerDetails(playerName);
        setPlayer(details);
        setLoading(false);
      } catch (err) {
        setError('Failed to load player details. Please try again later.');
        setLoading(false);
      }
    };

    if (playerName) {
      fetchPlayerDetails();
    }
  }, [playerName]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="bg-red-100 text-red-700 p-4 rounded-md mb-4">
          {error}
        </div>
        <button 
          onClick={() => window.history.back()}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!player) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="bg-yellow-100 text-yellow-700 p-4 rounded-md mb-4">
          Player not found.
        </div>
        <button 
          onClick={() => window.history.back()}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  const { batting, bowling, team, cost, is_capped } = player;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{playerName}</h1>
            <div className="flex items-center mt-2">
              <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">{team || 'Unknown Team'}</span>
              <span className="ml-2 bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
                {is_capped ? 'Capped' : 'Uncapped'}
              </span>
            </div>
          </div>
          <div className="mt-4 md:mt-0">
            <div className="text-xl font-bold text-green-600">₹{cost ? (cost / 10000000).toFixed(2) : 'N/A'} Cr</div>
            <div className="text-sm text-gray-500">Auction Price</div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Batting Stats */}
          {batting && (
            <div className="border rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-200">Batting Statistics</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Matches</div>
                  <div className="text-xl font-bold">{batting.Mat || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Innings</div>
                  <div className="text-xl font-bold">{batting.Inns || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Runs</div>
                  <div className="text-xl font-bold">{batting.Runs || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Average</div>
                  <div className="text-xl font-bold">{batting.Ave || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Strike Rate</div>
                  <div className="text-xl font-bold">{batting.SR || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">High Score</div>
                  <div className="text-xl font-bold">{batting.HS || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">50s</div>
                  <div className="text-xl font-bold">{batting['50'] || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">100s</div>
                  <div className="text-xl font-bold">{batting['100'] || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Ducks</div>
                  <div className="text-xl font-bold">{batting['0'] || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">4s</div>
                  <div className="text-xl font-bold">{batting['4s'] || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">6s</div>
                  <div className="text-xl font-bold">{batting['6s'] || 'N/A'}</div>
                </div>
              </div>
            </div>
          )}
          
          {/* Bowling Stats */}
          {bowling && (
            <div className="border rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-200">Bowling Statistics</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Matches</div>
                  <div className="text-xl font-bold">{bowling.Mat || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Innings</div>
                  <div className="text-xl font-bold">{bowling.Inns || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Wickets</div>
                  <div className="text-xl font-bold">{bowling.Wkts || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Average</div>
                  <div className="text-xl font-bold">{bowling.Ave || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Economy</div>
                  <div className="text-xl font-bold">{bowling.Econ || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Strike Rate</div>
                  <div className="text-xl font-bold">{bowling.SR || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Best Figures</div>
                  <div className="text-xl font-bold">{bowling.BBI || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">4w Hauls</div>
                  <div className="text-xl font-bold">{bowling['4'] || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">5w Hauls</div>
                  <div className="text-xl font-bold">{bowling['5'] || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Overs</div>
                  <div className="text-xl font-bold">{bowling.Overs || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Maidens</div>
                  <div className="text-xl font-bold">{bowling.Mdns || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Runs</div>
                  <div className="text-xl font-bold">{bowling.Runs || 'N/A'}</div>
                </div>
              </div>
            </div>
          )}
          
          {/* No Stats Available */}
          {!batting && !bowling && (
            <div className="col-span-full border rounded-lg p-4 bg-gray-50">
              <p className="text-gray-500 text-center">No statistics available for this player.</p>
            </div>
          )}
        </div>
        
        <div className="mt-6">
          <button 
            onClick={() => window.history.back()}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
};

export default PlayerDetailsPage;
