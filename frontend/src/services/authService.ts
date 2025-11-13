import { apiService } from './api';
import type { LoginRequest, SignupRequest, AuthResponse } from '../types';

export const authService = {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiService.getApi().post<AuthResponse>('/api/login', credentials);
    const { access_token, refresh_token } = response.data;
    apiService.setTokens(access_token, refresh_token);
    return response.data;
  },

  async signup(credentials: SignupRequest): Promise<AuthResponse> {
    const response = await apiService.getApi().post<AuthResponse>('/api/signup', credentials);
    const { access_token, refresh_token } = response.data;
    apiService.setTokens(access_token, refresh_token);
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await apiService.getApi().post('/api/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout error:', error);
    } finally {
      apiService.clearAuth();
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};

