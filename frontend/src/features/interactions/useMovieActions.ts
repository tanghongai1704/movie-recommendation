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
                interaction_action: 'open_detail',
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
                interaction_action: 'start',
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
                interaction_action: 'submit',
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

    const reactToMovie = useCallback(
        (movieId: string, reaction: 'like' | 'dislike'): boolean => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            void interactionState.recordInteraction({
                interaction_type: 'reaction',
                interaction_action: reaction,
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

    const shareMovie = useCallback(
        (movieId: string): boolean => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            void interactionState.recordInteraction({
                interaction_type: 'share',
                interaction_action: 'copy_link',
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

    return {
        ...interactionState,
        clickMovie,
        watchMovie,
        rateMovie,
        reactToMovie,
        shareMovie,
    };
}
