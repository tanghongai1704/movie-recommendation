import { useEffect, useState } from 'react';
import { movieService } from '../../services/movieService';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';
import type { Movie } from '../../types/api';

interface MovieDetailState {
    movie: Movie | null;
    status: AsyncStatus;
    error: string | null;
}

const initialState: MovieDetailState = {
    movie: null,
    status: 'idle',
    error: null,
};

export function useMovieDetail(movieId: string | null) {
    const [state, setState] = useState<MovieDetailState>(initialState);

    useEffect(() => {
        let cancelled = false;

        if (!movieId) {
            setState(initialState);
            return () => {
                cancelled = true;
            };
        }

        setState({ movie: null, status: 'loading', error: null });
        void movieService
            .getMovie(movieId)
            .then((movie) => {
                if (!cancelled) {
                    setState({ movie, status: 'success', error: null });
                }
            })
            .catch((error: unknown) => {
                if (!cancelled) {
                    setState({
                        movie: null,
                        status: 'error',
                        error: getErrorMessage(error, 'Unable to load movie details.'),
                    });
                }
            });

        return () => {
            cancelled = true;
        };
    }, [movieId]);

    return {
        ...state,
        isLoading: state.status === 'idle' || state.status === 'loading',
    };
}
