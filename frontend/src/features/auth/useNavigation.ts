import { useCallback, useEffect, useState } from 'react';

export type AppRoute = 'home' | 'login' | 'onboarding';

const routePaths: Record<AppRoute, string> = {
    home: '/',
    login: '/login',
    onboarding: '/onboarding',
};

function getRoute(pathname: string): AppRoute {
    if (pathname === routePaths.login) {
        return 'login';
    }
    if (pathname === routePaths.onboarding) {
        return 'onboarding';
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
