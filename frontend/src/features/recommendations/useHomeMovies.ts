import { useEffect, useMemo } from 'react';
import type { AuthUserState } from '../auth/useAuth';
import type { Movie } from '../../types/api';
import { useRecommendations } from './useRecommendations';

const HOME_RECOMMENDATION_LIMIT = 50;

interface UseHomeMoviesOptions {
    enabled: boolean;
    userState: AuthUserState;
    userId: string | null;
    catalogMovies: Movie[];
    catalogLoading: boolean;
    catalogError: string | null;
}

function mergeUniqueMovies(primary: Movie[], fallback: Movie[]): Movie[] {
    const seenIds = new Set<string>();
    return [...primary, ...fallback].filter((movie) => {
        if (seenIds.has(movie.movie_id)) {
            return false;
        }
        seenIds.add(movie.movie_id);
        return true;
    });
}

export function useHomeMovies({
    enabled,
    userState,
    userId,
    catalogMovies,
    catalogLoading,
    catalogError,
}: UseHomeMoviesOptions) {
    const recommendations = useRecommendations();
    const canLoadPersonalized =
        enabled && userState === 'returning-user' && userId !== null;

    useEffect(() => {
        if (!canLoadPersonalized || userId === null) {
            recommendations.clearRecommendations();
            return;
        }
        void recommendations.loadRecommendations(userId, {
            limit: HOME_RECOMMENDATION_LIMIT,
        });
    }, [
        canLoadPersonalized,
        recommendations.clearRecommendations,
        recommendations.loadRecommendations,
        userId,
    ]);

    const hasPersonalizedMovies =
        canLoadPersonalized &&
        recommendations.status === 'success' &&
        recommendations.recommendations.length > 0;

    const movies = useMemo(
        () =>
            hasPersonalizedMovies
                ? mergeUniqueMovies(
                      recommendations.recommendations,
                      catalogMovies,
                  )
                : catalogMovies,
        [
            catalogMovies,
            hasPersonalizedMovies,
            recommendations.recommendations,
        ],
    );

    const waitingForRecommendations =
        canLoadPersonalized &&
        (recommendations.status === 'idle' ||
            recommendations.status === 'loading');
    const isFallback =
        canLoadPersonalized &&
        (recommendations.status === 'error' ||
            (recommendations.status === 'success' &&
                recommendations.recommendations.length === 0));

    return {
        movies,
        isLoading:
            waitingForRecommendations ||
            (!hasPersonalizedMovies && catalogLoading),
        error: hasPersonalizedMovies ? null : catalogError,
        sectionTitle: hasPersonalizedMovies
            ? 'Movies for you'
            : 'Popular Now',
        fallbackNotice: isFallback
            ? `${
                  recommendations.error ||
                  'No personalized recommendations are available yet.'
              } Showing popular movies instead.`
            : null,
    };
}
