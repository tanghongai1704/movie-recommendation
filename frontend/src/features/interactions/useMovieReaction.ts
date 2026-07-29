import { useCallback, useEffect, useState } from 'react';
import { interactionService } from '../../services/interactionService';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

export type MovieReaction = 'like' | 'dislike';

interface MovieReactionState {
    reaction: MovieReaction | null;
    status: AsyncStatus;
    error: string | null;
}

interface UseMovieReactionOptions {
    movieId: string | null;
    canLoadReaction: boolean;
    onReact: (
        movieId: string,
        reaction: MovieReaction | null,
    ) => Promise<boolean>;
}

const initialState: MovieReactionState = {
    reaction: null,
    status: 'idle',
    error: null,
};

export function useMovieReaction({
    movieId,
    canLoadReaction,
    onReact,
}: UseMovieReactionOptions) {
    const [state, setState] = useState<MovieReactionState>(initialState);

    useEffect(() => {
        let isActive = true;

        if (!movieId || !canLoadReaction) {
            setState({
                reaction: null,
                status: 'success',
                error: null,
            });
            return () => {
                isActive = false;
            };
        }

        setState({
            reaction: null,
            status: 'loading',
            error: null,
        });
        void interactionService
            .getMyReaction(movieId)
            .then((response) => {
                if (isActive) {
                    setState({
                        reaction: response.reaction,
                        status: 'success',
                        error: null,
                    });
                }
            })
            .catch((error) => {
                if (isActive) {
                    setState({
                        reaction: null,
                        status: 'error',
                        error: getErrorMessage(
                            error,
                            'Unable to load your reaction.',
                        ),
                    });
                }
            });

        return () => {
            isActive = false;
        };
    }, [canLoadReaction, movieId]);

    const submitReaction = useCallback(
        async (reaction: MovieReaction): Promise<boolean> => {
            if (!movieId) {
                return false;
            }

            const nextReaction =
                state.reaction === reaction ? null : reaction;
            setState((current) => ({
                ...current,
                status: 'loading',
                error: null,
            }));
            const wasRecorded = await onReact(movieId, nextReaction);
            setState((current) => ({
                reaction: wasRecorded ? nextReaction : current.reaction,
                status: wasRecorded ? 'success' : 'error',
                error: wasRecorded
                    ? null
                    : current.error || 'Unable to save your reaction.',
            }));
            return wasRecorded;
        },
        [movieId, onReact, state.reaction],
    );

    return {
        ...state,
        isSubmitting: state.status === 'loading',
        submitReaction,
    };
}
