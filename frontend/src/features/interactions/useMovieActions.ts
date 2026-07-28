import { useCallback } from 'react';
import type { AuthUserState } from '../auth/useAuth';
import type { StaticAppRoute } from '../auth/useNavigation';
import { useInteractions } from './useInteractions';

type Navigate = (route: StaticAppRoute, replace?: boolean) => void;

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
            if (userState === 'guest') {
                return;
            }
            void interactionState.recordInteraction({
                interaction_type: 'click',
                movie_id: movieId,
            });
        },
        [interactionState.recordInteraction, userState],
    );

    const watchMovie = useCallback(
        (movieId: string): boolean => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            void interactionState.recordInteraction({
                interaction_type: 'watch',
                movie_id: movieId,
            });
            return true;
        },
        [
            handleAuthenticationRequired,
            interactionState.recordInteraction,
            userState,
        ],
    );

    const rateMovie = useCallback(
        (movieId: string, rating: number): boolean => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            void interactionState.recordInteraction({
                interaction_type: 'rating',
                movie_id: movieId,
                interaction_value: rating,
            });
            return true;
        },
        [
            handleAuthenticationRequired,
            interactionState.recordInteraction,
            userState,
        ],
    );

    return {
        ...interactionState,
        clickMovie,
        watchMovie,
        rateMovie,
    };
}
