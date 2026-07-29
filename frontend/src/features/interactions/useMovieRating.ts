import { useCallback, useEffect, useState } from 'react';
import { interactionService } from '../../services/interactionService';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

interface MovieRatingState {
    rating: number | null;
    status: AsyncStatus;
    error: string | null;
}

interface UseMovieRatingOptions {
    movieId: string | null;
    canLoadRating: boolean;
    onRate: (movieId: string, rating: number) => Promise<boolean>;
    onClear: (movieId: string) => Promise<boolean>;
}

const initialState: MovieRatingState = {
    rating: null,
    status: 'idle',
    error: null,
};

export function useMovieRating({
    movieId,
    canLoadRating,
    onRate,
    onClear,
}: UseMovieRatingOptions) {
    const [state, setState] = useState<MovieRatingState>(initialState);

    useEffect(() => {
        let isActive = true;

        if (!movieId || !canLoadRating) {
            setState({
                rating: null,
                status: 'success',
                error: null,
            });
            return () => {
                isActive = false;
            };
        }

        setState({
            rating: null,
            status: 'loading',
            error: null,
        });

        void interactionService
            .getMyRating(movieId)
            .then((response) => {
                if (isActive) {
                    setState({
                        rating: response.rating,
                        status: 'success',
                        error: null,
                    });
                }
            })
            .catch((error) => {
                if (isActive) {
                    setState({
                        rating: null,
                        status: 'error',
                        error: getErrorMessage(
                            error,
                            'Unable to load your rating.',
                        ),
                    });
                }
            });

        return () => {
            isActive = false;
        };
    }, [canLoadRating, movieId]);

    const submitRating = useCallback(
        async (rating: number): Promise<boolean> => {
            if (!movieId) {
                return false;
            }

            setState((current) => ({
                ...current,
                status: 'loading',
                error: null,
            }));
            const wasRecorded = await onRate(movieId, rating);
            setState((current) => ({
                rating: wasRecorded ? rating : current.rating,
                status: wasRecorded ? 'success' : 'error',
                error: wasRecorded
                    ? null
                    : current.error || 'Unable to save your rating.',
            }));
            return wasRecorded;
        },
        [movieId, onRate],
    );

    const clearRating = useCallback(async (): Promise<boolean> => {
        if (!movieId) {
            return false;
        }

        setState((current) => ({
            ...current,
            status: 'loading',
            error: null,
        }));
        const wasRecorded = await onClear(movieId);
        setState((current) => ({
            rating: wasRecorded ? null : current.rating,
            status: wasRecorded ? 'success' : 'error',
            error: wasRecorded
                ? null
                : current.error || 'Unable to clear your rating.',
        }));
        return wasRecorded;
    }, [movieId, onClear]);

    return {
        ...state,
        isLoading: state.status === 'loading',
        submitRating,
        clearRating,
    };
}
