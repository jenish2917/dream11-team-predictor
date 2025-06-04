import React from 'react';
import { Link } from 'react-router-dom';

const LoginPrompt = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
      <div className="w-full max-w-md p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center text-gray-800 dark:text-white mb-6">
          Authentication Required
        </h2>
        
        <div className="text-center mb-6">
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            You need to be logged in to access the Dream11 team predictor.
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center gap-4 mt-6">
            <Link
              to="/login"
              className="block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition"
            >
              Login
            </Link>
            
            <Link
              to="/signup"
              className="block px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 transition"
            >
              Sign Up
            </Link>
          </div>
        </div>
        
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-6">
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Dream11 Team Predictor helps you create optimal fantasy cricket teams based on player statistics and performance data.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPrompt;
