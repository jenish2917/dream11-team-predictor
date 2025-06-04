import React, { useState } from 'react';
import predictionService from '../../services/predictionService';

const DataLoader = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setMessage('');
      setError('');
      
      const result = await predictionService.loadCsvData();
      
      setMessage(`Data loaded successfully! Teams: ${result.teams_loaded}, Players: ${result.players_loaded}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load data from CSV files');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-8">
      <h2 className="text-xl font-bold mb-4">Data Management</h2>
      
      <div className="mb-4">
        <p className="text-gray-700 mb-2">
          Load player and team data from CSV files stored in the data/IPL-DATASET directory.
        </p>
        
        <button
          onClick={loadData}
          disabled={loading}
          className={`bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
            loading ? 'opacity-70 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Loading data...' : 'Load Data from CSV Files'}
        </button>
      </div>
      
      {message && (
        <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 my-4" role="alert">
          <p className="font-bold">Success!</p>
          <p>{message}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4" role="alert">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default DataLoader;
