import { useCallback, useEffect, useState } from 'react';

export type AppRoute = 'home' | 'login' | 'register' | 'onboarding' | 'profile';

const routePaths: Record<AppRoute, string> = {
    home: '/',
    login: '/login',
    register: '/register',
    onboarding: '/onboarding',
    profile: '/profile',
};

function getRoute(pathname: string): AppRoute {
    if (pathname === routePaths.login) {
        return 'login';
    }
    if (pathname === routePaths.register) {
        return 'register';
    }
    if (pathname === routePaths.onboarding) {
        return 'onboarding';
    }
    if (pathname === routePaths.profile) {
        return 'profile';
    }
    return 'home';
}

export function useNavigation() {
    const [route, setRoute] = useState<AppRoute>(() => getRoute(window.location.pathname));

    const navigate = useCallback((nextRoute: AppRoute, replace = false): void => {
        const path = routePaths[nextRoute];
        window.history[replace ? 'replaceState' : 'pushState']({}, '', path);
        setRoute(nextRoute);
    }, []);

    useEffect(() => {
        const handlePopState = () => setRoute(getRoute(window.location.pathname));
        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, []);

    return { route, navigate };
}
