import apiClient from './client';
import { LoginRequest, TokenResponse, User } from '../../types';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/api/auth/login', credentials);
    const { access_token, user } = response.data;
    
    // Store token and user
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/api/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  },

  validate: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/auth/validate');
    return response.data;
  },

  getStoredUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getStoredToken: (): string | null => {
    return localStorage.getItem('access_token');
  },
};
