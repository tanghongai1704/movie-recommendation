import { useCallback, useEffect, useState } from 'react';
import { movieService } from '../../services/movieService';
import type { Movie, MovieListParams } from '../../types/api';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

interface MoviesState {
    movies: Movie[];
    status: AsyncStatus;
    error: string | null;
}

const initialState: MoviesState = {
    movies: [],
    status: 'idle',
    error: null,
};

export function useMovies() {
    const [state, setState] = useState<MoviesState>(initialState);

    const loadMovies = useCallback(async (params: MovieListParams = {}): Promise<void> => {
        setState((current) => ({ ...current, status: 'loading', error: null }));

        try {
            const movies = await movieService.getMovies(params);
            setState({ movies, status: 'success', error: null });
        } catch (error) {
            setState((current) => ({
                ...current,
                status: 'error',
                error: getErrorMessage(error, 'Unable to load movies.'),
            }));
        }
    }, []);

    const getMovie = useCallback((movieId: string): Promise<Movie> => {
        return movieService.getMovie(movieId);
    }, []);

    useEffect(() => {
        void loadMovies();
    }, [loadMovies]);

    return {
        ...state,
        isLoading: state.status === 'idle' || state.status === 'loading',
        loadMovies,
        getMovie,
    };
}
