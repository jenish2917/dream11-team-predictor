import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, refreshTokenIfNeeded } = useAuth();
  const location = useLocation();
  const [isCheckingAuth, setIsCheckingAuth] = React.useState(true);

  // Effect to check authentication status when component mounts
  React.useEffect(() => {
    const checkAuth = async () => {
      try {
        // Try to refresh token if needed
        if (!isAuthenticated && !loading) {
          await refreshTokenIfNeeded();
        }
      } catch (err) {
        console.error("Authentication check failed:", err);
      } finally {
        setIsCheckingAuth(false);
      }
    };
    
    checkAuth();
  }, [isAuthenticated, loading, refreshTokenIfNeeded]);

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
  if (!isAuthenticated) {
    console.log('User not authenticated, redirecting to login');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  console.log('User authenticated, rendering protected content');
  return children;
};

export default ProtectedRoute;
