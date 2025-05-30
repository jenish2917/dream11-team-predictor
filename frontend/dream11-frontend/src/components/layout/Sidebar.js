import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';

const Sidebar = ({ collapsed, toggleSidebar }) => {
  const { darkMode, toggleTheme } = useTheme();
  const { logout } = useAuth();

  // Shared menu item styling for consistency
  const navItemClass = (isActive) => `
    flex items-center ${collapsed ? 'justify-center px-2' : 'px-4'} py-2.5 rounded-md
    transition-colors duration-150 ease-in-out
    ${isActive 
      ? 'bg-green-500 text-white font-medium' 
      : darkMode 
        ? 'text-gray-100 hover:bg-gray-700/60' 
        : 'text-gray-700 hover:bg-gray-200/70'
    }
    hover:shadow-sm
  `;

  return (
    <div className={`${collapsed ? 'w-16' : 'w-64'} h-full fixed left-0 top-0 ${darkMode ? 'bg-dark-background text-white' : 'bg-white text-gray-800'} ${collapsed ? 'px-2' : 'px-5'} py-6 flex flex-col shadow-lg transition-all duration-300 ease-in-out z-20`}>
      {/* Toggle Button */}
      <button 
        className="absolute top-6 -right-3 bg-green-500 text-white rounded-full p-1 shadow-md hover:bg-green-600 transition-colors duration-200"
        onClick={toggleSidebar}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <span className="material-icons text-sm">
          {collapsed ? 'chevron_right' : 'chevron_left'}
        </span>
      </button>

      {/* Logo Header */}
      <div className={`${collapsed ? 'text-xl' : 'text-2xl'} font-bold mb-8 flex items-center justify-center transition-all duration-200`}>
        <span className="text-green-500">{collapsed ? 'D11' : 'Dream11'}</span>
        {!collapsed && <span className="ml-1">Predictor</span>}
      </div>
      
      {/* Navigation Links */}
      <div className="flex-grow">
        <nav className="space-y-1">
          <NavLink 
            to="/dashboard" 
            className={({ isActive }) => navItemClass(isActive)}
            title="Dashboard"
          >
            <span className="material-icons text-xl mr-3">dashboard</span>
            {!collapsed && <span className="font-medium">Dashboard</span>}
          </NavLink>
          
          <NavLink 
            to="/history" 
            className={({ isActive }) => navItemClass(isActive)}
            title="History"
          >
            <span className="material-icons text-xl mr-3">history</span>
            {!collapsed && <span className="font-medium">History</span>}
          </NavLink>
          
          <NavLink 
            to="/settings" 
            className={({ isActive }) => navItemClass(isActive)}
            title="Settings"
          >
            <span className="material-icons text-xl mr-3">settings</span>
            {!collapsed && <span className="font-medium">Settings</span>}
          </NavLink>
        </nav>
      </div>
      
      {/* Footer Buttons */}
      <div className={`pt-4 mt-4 border-t border-gray-200 dark:border-gray-700 ${collapsed ? 'flex flex-col items-center' : ''}`}>
        <button 
          className={`
            w-full mb-2.5 ${collapsed ? 'px-2' : 'px-4'} py-2.5 rounded-md font-medium
            flex items-center ${collapsed ? 'justify-center' : ''}
            transition-all duration-200 ease-in-out
            ${darkMode 
              ? 'bg-gray-700 hover:bg-gray-600 text-white' 
              : 'bg-gray-100 hover:bg-gray-200 text-gray-800'}
          `}
          onClick={toggleTheme}
          title={darkMode ? 'Light Mode' : 'Dark Mode'}
        >
          <span className="material-icons text-xl mr-3">{darkMode ? 'light_mode' : 'dark_mode'}</span>
          {!collapsed && <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>}
        </button>
        
        <button 
          className={`
            w-full ${collapsed ? 'px-2' : 'px-4'} py-2.5 rounded-md font-medium
            bg-red-500 text-white hover:bg-red-600
            flex items-center ${collapsed ? 'justify-center' : ''}
            transition-all duration-200 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50
          `}
          onClick={logout}
          title="Logout"
        >
          <span className="material-icons text-xl mr-3">logout</span>
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
