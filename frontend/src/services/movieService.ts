import { apiClient } from '../api/apiClient';
import { frontendConfig } from '../config/environment';
import type { Movie, MovieListParams } from '../types/api';

const TMDB_POSTER_BASE_URL = frontendConfig.tmdbPosterBaseUrl;

function resolvePosterUrl(posterPath: string | null): string | null {
    const value = posterPath?.trim();
    if (!value) {
        return null;
    }
    if (/^https?:\/\//i.test(value) || /^(?:data|blob):/i.test(value)) {
        return value;
    }
    if (value.startsWith('//')) {
        return `https:${value}`;
    }
    return `${TMDB_POSTER_BASE_URL}/${value.replace(/^\/+/, '')}`;
}

export function normalizeMovie(movie: Movie): Movie {
    return {
        ...movie,
        poster_path: resolvePosterUrl(movie.poster_path),
    };
}

export const movieService = {
    async getMovies(params: MovieListParams = {}): Promise<Movie[]> {
        const movies = await apiClient.get<Movie[]>(
            '/movies',
            { ...params },
            { requiresAuth: false },
        );
        return movies.map(normalizeMovie);
    },

    async getMovie(movieId: string): Promise<Movie> {
        const movie = await apiClient.get<Movie>(`/movie/${movieId}`, undefined, {
            requiresAuth: false,
        });
        return normalizeMovie(movie);
    },
};
