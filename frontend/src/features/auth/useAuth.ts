import { useCallback, useEffect, useState } from 'react';
import { AUTH_UNAUTHORIZED_EVENT } from '../../api/apiClient';
import { authService } from '../../services/authService';
import type {
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserProfile,
} from '../../types/api';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

export type AuthUserState = 'guest' | 'first-login' | 'returning-user';

interface AuthState {
    user: UserProfile | null;
    userState: AuthUserState;
    status: AsyncStatus;
    error: string | null;
}

const guestState: AuthState = {
    user: null,
    userState: 'guest',
    status: 'success',
    error: null,
};

function getAuthenticatedState(user: UserProfile): AuthState {
    return {
        user,
        userState:
            user.user_state === 'returning_user'
                ? 'returning-user'
                : 'first-login',
        status: 'success',
        error: null,
    };
}

export function useAuth() {
    const [state, setState] = useState<AuthState>({
        ...guestState,
        status: 'idle',
    });

    const loadCurrentUser = useCallback(async (): Promise<UserProfile | null> => {
        if (!authService.hasAuthenticatedSession()) {
            setState(guestState);
            return null;
        }

        setState((current) => ({ ...current, status: 'loading', error: null }));

        try {
            const user = await authService.getCurrentUser();
            setState(getAuthenticatedState(user));
            return user;
        } catch {
            authService.clearSession();
            // Session restoration is best-effort. A stale token or a backend
            // restart should open the public experience without surfacing a
            // raw transport error on the login page.
            setState(guestState);
            return null;
        }
    }, []);

    const login = useCallback(
        async (credentials: LoginRequest): Promise<UserProfile | null> => {
            setState((current) => ({ ...current, status: 'loading', error: null }));

            try {
                const session = await authService.login(credentials);
                setState(getAuthenticatedState(session.user));
                return session.user;
            } catch (error) {
                authService.clearSession();
                setState({
                    ...guestState,
                    status: 'error',
                    error: getErrorMessage(error, 'Unable to sign in.'),
                });
                return null;
            }
        },
        [],
    );

    const register = useCallback(
        async (payload: RegisterRequest): Promise<UserProfile | null> => {
            setState((current) => ({ ...current, status: 'loading', error: null }));

            try {
                const session = await authService.register(payload);
                setState(getAuthenticatedState(session.user));
                return session.user;
            } catch (error) {
                authService.clearSession();
                setState({
                    ...guestState,
                    status: 'error',
                    error: getErrorMessage(error, 'Unable to create your account.'),
                });
                return null;
            }
        },
        [],
    );

    const completeOnboarding = useCallback(
        async (genres: string[]): Promise<UserProfile | null> => {
            setState((current) => ({ ...current, status: 'loading', error: null }));
            try {
                const user = await authService.completeOnboarding(genres);
                setState(getAuthenticatedState(user));
                return user;
            } catch (error) {
                setState((current) => ({
                    ...current,
                    status: 'error',
                    error: getErrorMessage(error, 'Unable to complete onboarding.'),
                }));
                return null;
            }
        },
        [],
    );

    const updateProfile = useCallback(
        async (payload: UpdateProfileRequest): Promise<UserProfile | null> => {
            setState((current) => ({ ...current, status: 'loading', error: null }));
            try {
                const user = await authService.updateProfile(payload);
                setState(getAuthenticatedState(user));
                return user;
            } catch (error) {
                setState((current) => ({
                    ...current,
                    status: 'error',
                    error: getErrorMessage(error, 'Unable to update your profile.'),
                }));
                return null;
            }
        },
        [],
    );

    const logout = useCallback(async (): Promise<void> => {
        try {
            await authService.logout();
        } finally {
            setState(guestState);
        }
    }, []);

    useEffect(() => {
        void loadCurrentUser();
    }, [loadCurrentUser]);

    useEffect(() => {
        const handleUnauthorized = (): void => setState(guestState);
        window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
        return () => {
            window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
        };
    }, []);

    return {
        ...state,
        isAuthenticated: state.userState !== 'guest',
        isRegisteredUser: state.user !== null,
        canCreateInteractions: state.userState !== 'guest',
        canAccessPersonalizedRecommendations:
            state.userState === 'returning-user',
        login,
        register,
        logout,
        completeOnboarding,
        updateProfile,
        loadCurrentUser,
    };
}
