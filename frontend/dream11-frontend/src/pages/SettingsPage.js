import React, { useState } from 'react';
import MainLayout from '../components/layout/MainLayout';

const SettingsPage = () => {
  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: false,
    defaultTeamType: 'balanced',
    dataPrivacy: 'private'
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setPreferences({
      ...preferences,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // This would save settings to backend
    alert('Settings saved successfully!');
  };

  return (
    <MainLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4 dark:text-white">Settings</h1>
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Account Settings</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="block text-gray-700 dark:text-gray-300">Email</label>
                  <input 
                    type="email" 
                    className="ml-4 p-2 border rounded-md bg-gray-50 dark:bg-gray-700 dark:border-gray-600 text-gray-900 dark:text-white" 
                    defaultValue="user@example.com"
                    disabled
                  />
                </div>
                <div>
                  <button 
                    type="button" 
                    className="text-indigo-600 dark:text-indigo-400 hover:underline focus:outline-none"
                  >
                    Change Password
                  </button>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Notifications</h2>
              <div className="space-y-3">
                <div className="flex items-center">
                  <input 
                    id="emailNotifications" 
                    name="emailNotifications"
                    type="checkbox" 
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={preferences.emailNotifications}
                    onChange={handleChange} 
                  />
                  <label htmlFor="emailNotifications" className="ml-3 block text-gray-700 dark:text-gray-300">
                    Email Notifications
                  </label>
                </div>
                <div className="flex items-center">
                  <input 
                    id="pushNotifications" 
                    name="pushNotifications"
                    type="checkbox" 
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={preferences.pushNotifications}
                    onChange={handleChange}
                  />
                  <label htmlFor="pushNotifications" className="ml-3 block text-gray-700 dark:text-gray-300">
                    Push Notifications
                  </label>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Prediction Preferences</h2>
              <div>
                <label className="block text-gray-700 dark:text-gray-300 mb-2">Default Team Type</label>
                <select 
                  name="defaultTeamType"
                  value={preferences.defaultTeamType}
                  onChange={handleChange}
                  className="block w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="aggressive">Aggressive</option>
                  <option value="balanced">Balanced</option>
                  <option value="riskAverse">Risk-Averse</option>
                </select>
              </div>
            </div>
            
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">Privacy Settings</h2>
              <div>
                <label className="block text-gray-700 dark:text-gray-300 mb-2">Data Privacy</label>
                <select 
                  name="dataPrivacy"
                  value={preferences.dataPrivacy}
                  onChange={handleChange}
                  className="block w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="private">Private - Only visible to me</option>
                  <option value="friends">Friends - Visible to my connections</option>
                  <option value="public">Public - Visible to all users</option>
                </select>
              </div>
            </div>
            
            <div className="flex justify-end">
              <button 
                type="submit" 
                className="bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded focus:outline-none focus:shadow-outline-indigo"
              >
                Save Settings
              </button>
            </div>
          </form>
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
