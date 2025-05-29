import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';

const Sidebar = () => {
  const { darkMode, toggleTheme } = useTheme();
  const { logout } = useAuth();
  
  return (
    <div className={`w-64 h-full fixed left-0 top-0 ${darkMode ? 'bg-dark-background text-white' : 'bg-gray-100 text-gray-800'} p-4 flex flex-col shadow-lg`}>
      <div className="text-2xl font-bold mb-6 flex items-center justify-center">
        <span className="text-green-500">Dream11</span>
        <span className="ml-1">Predictor</span>
      </div>
      
      <div className="flex-grow">
        <nav className="space-y-2">
          <NavLink 
            to="/dashboard" 
            className={({ isActive }) => 
              `flex items-center p-3 rounded-md ${isActive 
                ? 'bg-green-500 text-white' 
                : darkMode 
                  ? 'hover:bg-gray-700' 
                  : 'hover:bg-gray-200'}`
            }
          >
            <span className="material-icons mr-2">dashboard</span>
            <span>Dashboard</span>
          </NavLink>
          
          <NavLink 
            to="/history" 
            className={({ isActive }) => 
              `flex items-center p-3 rounded-md ${isActive 
                ? 'bg-green-500 text-white' 
                : darkMode 
                  ? 'hover:bg-gray-700' 
                  : 'hover:bg-gray-200'}`
            }
          >
            <span className="material-icons mr-2">history</span>
            <span>History</span>
          </NavLink>
          
          <NavLink 
            to="/settings" 
            className={({ isActive }) => 
              `flex items-center p-3 rounded-md ${isActive 
                ? 'bg-green-500 text-white' 
                : darkMode 
                  ? 'hover:bg-gray-700' 
                  : 'hover:bg-gray-200'}`
            }
          >
            <span className="material-icons mr-2">settings</span>
            <span>Settings</span>
          </NavLink>
        </nav>
      </div>
      
      <div className="pt-4 border-t border-gray-600">
        <button 
          className={`w-full p-3 rounded-md ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} flex items-center justify-center mb-3`}
          onClick={toggleTheme}
        >
          <span className="material-icons mr-2">{darkMode ? 'light_mode' : 'dark_mode'}</span>
          <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
        
        <button 
          className="w-full p-3 rounded-md bg-red-500 text-white hover:bg-red-600 flex items-center justify-center"
          onClick={logout}
        >
          <span className="material-icons mr-2">logout</span>
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
