import { apiClient } from '../api/apiClient';
import type {
    CreateInteractionInput,
    CreateInteractionRequest,
    Interaction,
    UserMovieRating,
    UserMovieReaction,
} from '../types/api';

const SESSION_STORAGE_KEY = 'movie-recommendation.session-id';

function getSessionId(): string {
    const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (existing) {
        return existing;
    }

    const sessionId = window.crypto.randomUUID();
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    return sessionId;
}

export const interactionService = {
    getMyRating(movieId: string): Promise<UserMovieRating> {
        return apiClient.get<UserMovieRating>(
            `/users/me/ratings/${encodeURIComponent(movieId)}`,
        );
    },

    getMyReaction(movieId: string): Promise<UserMovieReaction> {
        return apiClient.get<UserMovieReaction>(
            `/users/me/reactions/${encodeURIComponent(movieId)}`,
        );
    },

    async createInteraction(
        interaction: CreateInteractionInput,
    ): Promise<Interaction> {
        const idempotencyKey = window.crypto.randomUUID();
        const request: CreateInteractionRequest = {
            ...interaction,
            timestamp: new Date().toISOString(),
            session_id: getSessionId(),
        };
        const send = (): Promise<Interaction> =>
            apiClient.post<Interaction, CreateInteractionRequest>(
                '/users/me/interactions',
                request,
                {
                    headers: {
                        'Idempotency-Key': idempotencyKey,
                    },
                },
            );

        try {
            return await send();
        } catch (error) {
            if (error instanceof TypeError) {
                return send();
            }
            throw error;
        }
    },
};
