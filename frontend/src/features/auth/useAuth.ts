import { useCallback, useEffect, useState } from 'react';
import { authService } from '../../services/authService';
import type { LoginRequest, UserProfile } from '../../types/api';
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
    const onboardingCompleted = authService.isOnboardingCompleted(user.username);

    return {
        user,
        userState: onboardingCompleted ? 'returning-user' : 'first-login',
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
        } catch (error) {
            authService.logout();
            setState({
                ...guestState,
                error: getErrorMessage(error, 'Your session has expired.'),
            });
            return null;
        }
    }, []);

    const login = useCallback(async (credentials: LoginRequest): Promise<UserProfile | null> => {
        setState((current) => ({ ...current, status: 'loading', error: null }));

        try {
            await authService.login(credentials);
            const user = await authService.getCurrentUser();
            setState(getAuthenticatedState(user));
            return user;
        } catch (error) {
            authService.logout();
            setState({
                ...guestState,
                status: 'error',
                error: getErrorMessage(error, 'Unable to sign in.'),
            });
            return null;
        }
    }, []);

    const completeOnboarding = useCallback((): void => {
        setState((current) => {
            if (!current.user) {
                return current;
            }

            authService.completeOnboarding(current.user.username);
            return {
                ...current,
                userState: 'returning-user',
                status: 'success',
                error: null,
            };
        });
    }, []);

    const logout = useCallback((): void => {
        authService.logout();
        setState(guestState);
    }, []);

    useEffect(() => {
        void loadCurrentUser();
    }, [loadCurrentUser]);

    return {
        ...state,
        isAuthenticated: state.userState !== 'guest',
        canCreateInteractions: state.userState === 'returning-user',
        login,
        logout,
        completeOnboarding,
        loadCurrentUser,
    };
}
