import { apiClient } from '../api/apiClient';
import type { RecommendationParams, RecommendationResponse } from '../types/api';
import { normalizeMovie } from './movieService';

export const recommendationService = {
    async getRecommendations(
        userId: string,
        params: RecommendationParams = {},
    ): Promise<RecommendationResponse> {
        const response = await apiClient.get<RecommendationResponse>(
            `/recommend/${userId}`,
            { ...params },
        );
        return {
            ...response,
            recommendations: response.recommendations.map((item) => ({
                ...normalizeMovie(item),
                score: item.score,
                reason_code: item.reason_code,
            })),
        };
    },
};
