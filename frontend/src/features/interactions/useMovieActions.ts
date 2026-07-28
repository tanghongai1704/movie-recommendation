import { useCallback } from 'react';
import type { AuthUserState } from '../auth/useAuth';
import type { AppRoute } from '../auth/useNavigation';
import { useInteractions } from './useInteractions';

type Navigate = (route: AppRoute, replace?: boolean) => void;

export function useMovieActions(userState: AuthUserState, navigate: Navigate) {
    const handleAuthenticationRequired = useCallback((): void => {
        navigate('login');
    }, [navigate]);

    const interactionState = useInteractions({
        canCreate: userState !== 'guest',
        onAuthenticationRequired: handleAuthenticationRequired,
    });

    const clickMovie = useCallback(
        (movieId: string): void => {
            void interactionState.recordInteraction({
                interaction_type: 'click',
                movie_id: movieId,
            });
        },
        [interactionState.recordInteraction],
    );

    const watchMovie = useCallback(
        (movieId: string): void => {
            void interactionState.recordInteraction({
                interaction_type: 'watch',
                movie_id: movieId,
            });
        },
        [interactionState.recordInteraction],
    );

    const rateMovie = useCallback(
        (movieId: string, rating: number): void => {
            void interactionState.recordInteraction({
                interaction_type: 'rating',
                movie_id: movieId,
                interaction_value: rating,
            });
        },
        [interactionState.recordInteraction],
    );

    return {
        ...interactionState,
        clickMovie,
        watchMovie,
        rateMovie,
    };
}
