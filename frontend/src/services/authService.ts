import { apiClient } from '../api/apiClient';
import type { LoginRequest, TokenResponse, UserProfile } from '../types/api';

const ONBOARDING_STORAGE_PREFIX = 'movie-recommendation.onboarding-completed';

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

    hasAuthenticatedSession(): boolean {
        return apiClient.hasAuthenticatedSession();
    },

    isOnboardingCompleted(username: string): boolean {
        return window.localStorage.getItem(`${ONBOARDING_STORAGE_PREFIX}.${username}`) === 'true';
    },

    completeOnboarding(username: string): void {
        window.localStorage.setItem(`${ONBOARDING_STORAGE_PREFIX}.${username}`, 'true');
    },

    logout(): void {
        apiClient.clearAccessToken();
    },
};
