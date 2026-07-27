import { apiClient } from '../api/apiClient';
import type { RecommendationParams, RecommendationResponse } from '../types/api';

export const recommendationService = {
    getRecommendations(
        params: RecommendationParams = {},
    ): Promise<RecommendationResponse> {
        return apiClient.get<RecommendationResponse>('/recommendations', { ...params });
    },
};
