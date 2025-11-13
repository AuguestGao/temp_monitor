import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { authService } from '../services/authService';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated on mount
    const checkAuth = () => {
      const isAuthenticated = authService.isAuthenticated();
      if (isAuthenticated) {
        // Extract username from token (basic implementation)
        // In a real app, you might want to decode the JWT or have a /me endpoint
        const accessToken = localStorage.getItem('access_token');
        if (accessToken) {
          try {
            // Decode JWT payload (simple base64 decode)
            const payload = JSON.parse(atob(accessToken.split('.')[1]));
            setUser({ username: payload.username });
          } catch (error) {
            console.error('Error decoding token:', error);
            authService.logout();
          }
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    await authService.login({ username, password });
    setUser({ username });
  };

  const signup = async (username: string, password: string) => {
    await authService.signup({ username, password });
    setUser({ username });
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

