import { useCallback, useState } from 'react';
import { recommendationService } from '../../services/recommendationService';
import type {
    RecommendationItem,
    RecommendationParams,
    RecommendationResponse,
} from '../../types/api';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

interface RecommendationsState {
    userId: string | null;
    recommendations: RecommendationItem[];
    status: AsyncStatus;
    error: string | null;
}

const initialState: RecommendationsState = {
    userId: null,
    recommendations: [],
    status: 'idle',
    error: null,
};

export function useRecommendations() {
    const [state, setState] = useState<RecommendationsState>(initialState);

    const loadRecommendations = useCallback(
        async (
            userId: string,
            params: RecommendationParams = {},
        ): Promise<RecommendationResponse | null> => {
            setState((current) => ({ ...current, status: 'loading', error: null }));

            try {
                const response = await recommendationService.getRecommendations(
                    userId,
                    params,
                );
                setState({
                    userId: response.user_id,
                    recommendations: response.recommendations,
                    status: 'success',
                    error: null,
                });
                return response;
            } catch (error) {
                setState((current) => ({
                    ...current,
                    status: 'error',
                    error: getErrorMessage(error, 'Unable to load recommendations.'),
                }));
                return null;
            }
        },
        [],
    );

    const clearRecommendations = useCallback((): void => {
        setState(initialState);
    }, []);

    return {
        ...state,
        isLoading: state.status === 'loading',
        loadRecommendations,
        clearRecommendations,
    };
}
