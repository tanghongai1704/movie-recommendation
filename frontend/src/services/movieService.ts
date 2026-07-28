import { apiClient } from '../api/apiClient';
import type { Movie, MovieListParams } from '../types/api';

export const movieService = {
    getMovies(params: MovieListParams = {}): Promise<Movie[]> {
        return apiClient.get<Movie[]>('/movies', { ...params }, { requiresAuth: false });
    },

    getMovie(movieId: string): Promise<Movie> {
        return apiClient.get<Movie>(`/movie/${movieId}`, undefined, {
            requiresAuth: false,
        });
    },
};
