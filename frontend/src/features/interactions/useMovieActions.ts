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
                interaction_action: 'record',
                movie_id: movieId,
                interaction_value: 1,
            });
        },
        [interactionState.recordInteraction, userState],
    );

    const canWatchMovie = useCallback(
        (): boolean => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            return true;
        },
        [handleAuthenticationRequired, userState],
    );

    const recordWatchProgress = useCallback(
        (movieId: string, progress: number): void => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return;
            }
            void interactionState.recordInteraction({
                interaction_type: 'watch',
                interaction_action: 'record',
                movie_id: movieId,
                interaction_value: progress,
            });
        },
        [
            handleAuthenticationRequired,
            interactionState.recordInteraction,
            userState,
        ],
    );

    const rateMovie = useCallback(
        async (movieId: string, rating: number): Promise<boolean> => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            const interaction = await interactionState.recordInteraction({
                interaction_type: 'rating',
                interaction_action: 'set',
                movie_id: movieId,
                interaction_value: rating,
            });
            return interaction !== null;
        },
        [
            handleAuthenticationRequired,
            interactionState.recordInteraction,
            userState,
        ],
    );

    const clearMovieRating = useCallback(
        async (movieId: string): Promise<boolean> => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            const interaction = await interactionState.recordInteraction({
                interaction_type: 'rating',
                interaction_action: 'clear',
                movie_id: movieId,
                interaction_value: 0,
            });
            return interaction !== null;
        },
        [
            handleAuthenticationRequired,
            interactionState.recordInteraction,
            userState,
        ],
    );

    const reactToMovie = useCallback(
        async (
            movieId: string,
            reaction: 'like' | 'dislike' | null,
        ): Promise<boolean> => {
            if (userState === 'guest') {
                handleAuthenticationRequired();
                return false;
            }
            const interaction = await interactionState.recordInteraction({
                interaction_type: 'reaction',
                interaction_action: reaction === null ? 'clear' : 'set',
                movie_id: movieId,
                interaction_value:
                    reaction === null ? 0 : reaction === 'like' ? 1 : -1,
            });
            return interaction !== null;
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
                interaction_action: 'record',
                movie_id: movieId,
                interaction_value: 1,
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
        canWatchMovie,
        recordWatchProgress,
        rateMovie,
        clearMovieRating,
        reactToMovie,
        shareMovie,
    };
}
