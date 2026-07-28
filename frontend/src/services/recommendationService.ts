import { apiClient } from '../api/apiClient';
import type { RecommendationParams, RecommendationResponse } from '../types/api';

export const recommendationService = {
    getRecommendations(
        userId: string,
        params: RecommendationParams = {},
    ): Promise<RecommendationResponse> {
        return apiClient.get<RecommendationResponse>(
            `/recommend/${userId}`,
            { ...params },
        );
    },
};
