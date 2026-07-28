import { useEffect } from 'react';
import type { AuthUserState } from './useAuth';
import type { AppRoute } from './useNavigation';

export function useAuthRouting(
    userState: AuthUserState,
    authReady: boolean,
    route: AppRoute,
    navigate: (route: AppRoute, replace?: boolean) => void,
): void {
    useEffect(() => {
        if (!authReady) {
            return;
        }

        if (userState === 'first-login' && route !== 'onboarding') {
            navigate('onboarding', true);
            return;
        }

        if (
            userState === 'returning-user'
            && (route === 'login' || route === 'register' || route === 'onboarding')
        ) {
            navigate('home', true);
            return;
        }

        if (
            userState === 'guest'
            && (route === 'onboarding' || route === 'profile')
        ) {
            navigate('login', true);
        }
    }, [authReady, navigate, route, userState]);
}
