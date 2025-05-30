import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import jwt_decode from 'jwt-decode';
import { authService } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token') || null);
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token') || null);
  const [loading, setLoading] = useState(true);

  // Check if token is expired
  const isTokenExpired = useCallback((token) => {
    if (!token) return true;
    
    try {
      const decodedToken = jwt_decode(token);
      const currentTime = Date.now() / 1000;
      return decodedToken.exp < currentTime;
    } catch (error) {
      console.error("Invalid token format:", error);
      return true;
    }
  }, []);
  // Refresh token if needed
  const refreshTokenIfNeeded = useCallback(async () => {
    if (!refreshToken) return false;
    
    try {
      // Check if current access token is expired
      if (token && !isTokenExpired(token)) {
        return true; // Token still valid
      }
      
      // Try to refresh token
      const newAccessToken = await authService.refreshToken();
      
      if (!newAccessToken) {
        throw new Error('Failed to get new access token');
      }
      
      // Update state with new token
      setToken(newAccessToken);
      
      // Update user data from the refreshed token
      try {
        const decodedUser = jwt_decode(newAccessToken);
        setUser(decodedUser);
      } catch (decodeError) {
        console.error("Failed to decode new token:", decodeError);
        throw new Error('Invalid token format');
      }
      
      return true;
    } catch (error) {
      console.error("Failed to refresh token:", error);
      // Clear invalid tokens
      logout(); 
      return false;
    }
  }, [token, refreshToken, isTokenExpired]);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to use the stored token
        if (token) {
          // If token is valid, set user
          if (!isTokenExpired(token)) {
            const decodedUser = jwt_decode(token);
            setUser(decodedUser);
          } else if (refreshToken) {
            // Try to refresh token if expired
            await refreshTokenIfNeeded();
          } else {
            logout(); // No valid token or refresh token
          }
        }
      } catch (error) {
        console.error("Auth initialization error:", error);
        logout();
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, [token, refreshToken, isTokenExpired, refreshTokenIfNeeded]);
  // Login function
  const login = (accessToken, refreshToken) => {
    if (!accessToken || !refreshToken) {
      console.error("Missing tokens during login");
      return false;
    }
    
    try {
      // First try to decode the token to verify it's valid
      const decodedUser = jwt_decode(accessToken);
      
      // If successful, proceed with setting tokens
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      
      setToken(accessToken);
      setRefreshToken(refreshToken);
      setUser(decodedUser);
      
      console.log("Login successful, user set:", decodedUser);
      return true;
    } catch (error) {
      console.error("Failed to decode token during login:", error);
      return false;
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setRefreshToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token && !!user,
        user,
        token,
        refreshToken,
        login,
        logout,
        loading,
        refreshTokenIfNeeded
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
