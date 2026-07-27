import { useCallback, useState } from 'react';
import { authService } from '../../services/authService';
import type { LoginRequest, UserProfile } from '../../types/api';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

interface AuthState {
    user: UserProfile | null;
    status: AsyncStatus;
    error: string | null;
}

const initialState: AuthState = {
    user: null,
    status: 'idle',
    error: null,
};

export function useAuth() {
    const [state, setState] = useState<AuthState>(initialState);

    const loadCurrentUser = useCallback(async (): Promise<UserProfile | null> => {
        setState((current) => ({ ...current, status: 'loading', error: null }));

        try {
            const user = await authService.getCurrentUser();
            setState({ user, status: 'success', error: null });
            return user;
        } catch (error) {
            setState({
                user: null,
                status: 'error',
                error: getErrorMessage(error, 'Unable to load the current user.'),
            });
            return null;
        }
    }, []);

    const login = useCallback(async (credentials: LoginRequest): Promise<UserProfile | null> => {
        setState((current) => ({ ...current, status: 'loading', error: null }));

        try {
            await authService.login(credentials);
            const user = await authService.getCurrentUser();
            setState({ user, status: 'success', error: null });
            return user;
        } catch (error) {
            authService.logout();
            setState({
                user: null,
                status: 'error',
                error: getErrorMessage(error, 'Unable to sign in.'),
            });
            return null;
        }
    }, []);

    const logout = useCallback((): void => {
        authService.logout();
        setState(initialState);
    }, []);

    return {
        ...state,
        isAuthenticated: state.user !== null,
        login,
        logout,
        loadCurrentUser,
    };
}
