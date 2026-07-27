import { apiClient } from '../api/apiClient';
import type { LoginRequest, TokenResponse, UserProfile } from '../types/api';

export const authService = {
    async login(credentials: LoginRequest): Promise<TokenResponse> {
        const token = await apiClient.post<TokenResponse, LoginRequest>(
            '/auth/login',
            credentials,
            { requiresAuth: false },
        );
        apiClient.setAccessToken(token.access_token);
        return token;
    },

    getCurrentUser(): Promise<UserProfile> {
        return apiClient.get<UserProfile>('/auth/me');
    },

    logout(): void {
        apiClient.clearAccessToken();
    },
};
