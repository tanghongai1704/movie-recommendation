import { apiClient } from '../api/apiClient';
import type { CreateInteractionRequest, Interaction } from '../types/api';

export const interactionService = {
    createInteraction(interaction: CreateInteractionRequest): Promise<Interaction> {
        return apiClient.post<Interaction, CreateInteractionRequest>(
            '/users/me/interactions',
            interaction,
        );
    },
};
