import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import DataLoader from '../components/admin/DataLoader';
import TeamPredictor from '../components/predictor/TeamPredictor';

const Dashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('predict');

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Welcome back, {user?.username || 'User'}!
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('predict')}
              className={`${
                activeTab === 'predict'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Team Predictor
            </button>
            <button
              onClick={() => setActiveTab('data')}
              className={`${
                activeTab === 'data'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Data Management
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`${
                activeTab === 'history'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Prediction History
            </button>
          </nav>
        </div>

        {/* Tab content */}
        <div>
          {activeTab === 'predict' && <TeamPredictor />}
          {activeTab === 'data' && <DataLoader />}
          {activeTab === 'history' && (
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Prediction History</h2>
              <p>Your previous predictions will appear here.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
