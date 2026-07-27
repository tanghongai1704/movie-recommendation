import { useCallback } from 'react';
import type { AuthUserState } from '../auth/useAuth';
import type { AppRoute } from '../auth/useNavigation';
import { useInteractions } from './useInteractions';

type Navigate = (route: AppRoute, replace?: boolean) => void;

export function useMovieActions(userState: AuthUserState, navigate: Navigate) {
    const handleAuthenticationRequired = useCallback((): void => {
        navigate(userState === 'guest' ? 'login' : 'onboarding');
    }, [navigate, userState]);

    const interactionState = useInteractions({
        canCreate: userState === 'returning-user',
        onAuthenticationRequired: handleAuthenticationRequired,
    });

    const watchMovie = useCallback(
        (movieId: number): void => {
            void interactionState.recordInteraction({
                event_type: 'view',
                movie_id: movieId,
                metadata: { source: 'ui' },
            });
        },
        [interactionState.recordInteraction],
    );

    const rateMovie = useCallback(
        (movieId: number, rating: number): void => {
            void interactionState.recordInteraction({
                event_type: 'rating',
                movie_id: movieId,
                rating,
                metadata: { source: 'ui' },
            });
        },
        [interactionState.recordInteraction],
    );

    return {
        ...interactionState,
        watchMovie,
        rateMovie,
    };
}
