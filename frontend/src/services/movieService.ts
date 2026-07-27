import { apiClient } from '../api/apiClient';
import type { Movie, MovieListParams } from '../types/api';

export const movieService = {
    getMovies(params: MovieListParams = {}): Promise<Movie[]> {
        return apiClient.get<Movie[]>('/movies', { ...params }, { allowGuest: true });
    },

    getMovie(movieId: number): Promise<Movie> {
        return apiClient.get<Movie>(`/movies/${movieId}`, undefined, { allowGuest: true });
    },
};
