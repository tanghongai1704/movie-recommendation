import { apiClient } from '../api/apiClient';
import type {
    CompleteOnboardingRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
} from '../types/api';

async function createSession(
    path: '/auth/login' | '/auth/register',
    credentials: LoginRequest | RegisterRequest,
): Promise<TokenResponse> {
    const session = await apiClient.post<
        TokenResponse,
        LoginRequest | RegisterRequest
    >(path, credentials, { requiresAuth: false });
    apiClient.setAccessToken(session.access_token);
    return session;
}

export const authService = {
    register(credentials: RegisterRequest): Promise<TokenResponse> {
        return createSession('/auth/register', credentials);
    },

    login(credentials: LoginRequest): Promise<TokenResponse> {
        return createSession('/auth/login', credentials);
    },

    getCurrentUser(): Promise<UserProfile> {
        return apiClient.get<UserProfile>('/auth/me');
    },

    updateProfile(payload: UpdateProfileRequest): Promise<UserProfile> {
        return apiClient.patch<UserProfile, UpdateProfileRequest>(
            '/users/me/profile',
            payload,
        );
    },

    completeOnboarding(genres: string[]): Promise<UserProfile> {
        return apiClient.put<UserProfile, CompleteOnboardingRequest>(
            '/users/me/onboarding',
            { onboarding_genres: genres },
        );
    },

    hasAuthenticatedSession(): boolean {
        return apiClient.hasAuthenticatedSession();
    },

    async logout(): Promise<void> {
        try {
            if (apiClient.hasAuthenticatedSession()) {
                await apiClient.post<void>('/auth/logout');
            }
        } finally {
            apiClient.clearAccessToken();
        }
    },

    clearSession(): void {
        apiClient.clearAccessToken();
    },
};
