import { useCallback, useEffect, useState } from 'react';

export type StaticAppRoute =
    | 'home'
    | 'login'
    | 'register'
    | 'onboarding'
    | 'profile';
export type AppRoute = StaticAppRoute | 'movie-detail';

const routePaths: Record<StaticAppRoute, string> = {
    home: '/',
    login: '/login',
    register: '/register',
    onboarding: '/onboarding',
    profile: '/profile',
};
const movieDetailPrefix = '/movies/';

interface NavigationState {
    route: AppRoute;
    movieId: string | null;
}

function getNavigationState(pathname: string): NavigationState {
    if (pathname === routePaths.login) {
        return { route: 'login', movieId: null };
    }
    if (pathname === routePaths.register) {
        return { route: 'register', movieId: null };
    }
    if (pathname === routePaths.onboarding) {
        return { route: 'onboarding', movieId: null };
    }
    if (pathname === routePaths.profile) {
        return { route: 'profile', movieId: null };
    }
    if (pathname.startsWith(movieDetailPrefix)) {
        const encodedMovieId = pathname.slice(movieDetailPrefix.length);
        if (encodedMovieId) {
            try {
                return {
                    route: 'movie-detail',
                    movieId: decodeURIComponent(encodedMovieId),
                };
            } catch {
                return { route: 'home', movieId: null };
            }
        }
    }
    return { route: 'home', movieId: null };
}

export function useNavigation() {
    const [navigation, setNavigation] = useState<NavigationState>(() =>
        getNavigationState(window.location.pathname),
    );

    const navigate = useCallback((nextRoute: StaticAppRoute, replace = false): void => {
        const path = routePaths[nextRoute];
        window.history[replace ? 'replaceState' : 'pushState']({}, '', path);
        setNavigation({ route: nextRoute, movieId: null });
    }, []);

    const navigateToMovie = useCallback((movieId: string, replace = false): void => {
        const path = `${movieDetailPrefix}${encodeURIComponent(movieId)}`;
        window.history[replace ? 'replaceState' : 'pushState']({}, '', path);
        setNavigation({ route: 'movie-detail', movieId });
    }, []);

    useEffect(() => {
        const handlePopState = () =>
            setNavigation(getNavigationState(window.location.pathname));
        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, []);

    return {
        ...navigation,
        navigate,
        navigateToMovie,
    };
}
