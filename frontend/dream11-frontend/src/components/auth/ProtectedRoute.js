import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoginPrompt from './LoginPrompt';

const ProtectedRoute = ({ children }) => {
  const { isLoggedIn, loading } = useAuth();
  const location = useLocation();
  const [isCheckingAuth, setIsCheckingAuth] = React.useState(true);
  // Effect to check authentication status when component mounts
  React.useEffect(() => {
    // Simple check to see if user is logged in
    const checkAuth = async () => {
      // Short delay to ensure auth state is loaded
      setTimeout(() => {
        setIsCheckingAuth(false);
      }, 500);
    };
    
    checkAuth();
  }, [loading]);

  // Show loading state while checking authentication
  if (loading || isCheckingAuth) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-300">Verifying your session...</p>
      </div>
    );
  }
  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    console.log('User not authenticated, showing login prompt');
    return <LoginPrompt />;
  }

  console.log('User authenticated, rendering protected content');
  return children;
};

export default ProtectedRoute;
