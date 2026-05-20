import apiClient from './axios';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types';

export const authApi = {
  /**
   * Register a new user
   */
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post('/api/v1/auth/register', data);
    return response.data;
  },

  /**
   * Login user and get tokens
   */
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    // OAuth2 expects form data with username/email and password
    const formData = new FormData();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const response = await apiClient.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * Get current user profile
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: { full_name?: string }): Promise<User> => {
    const response = await apiClient.put('/api/v1/auth/me', data);
    return response.data;
  },

  /**
   * Change password
   */
  changePassword: async (oldPassword: string, newPassword: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/api/v1/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};
