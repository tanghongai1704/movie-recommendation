import { apiClient } from '../api/apiClient';
import type {
    CreateInteractionInput,
    CreateInteractionRequest,
    Interaction,
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
    createInteraction(interaction: CreateInteractionInput): Promise<Interaction> {
        return apiClient.post<Interaction, CreateInteractionRequest>(
            '/users/me/interactions',
            {
                ...interaction,
                session_id: getSessionId(),
            },
        );
    },
};
