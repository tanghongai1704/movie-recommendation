import { useCallback, useState } from 'react';
import { interactionService } from '../../services/interactionService';
import type { CreateInteractionRequest, Interaction } from '../../types/api';
import { getErrorMessage, type AsyncStatus } from '../../state/asyncState';

interface InteractionsState {
    interactions: Interaction[];
    status: AsyncStatus;
    error: string | null;
}

const initialState: InteractionsState = {
    interactions: [],
    status: 'idle',
    error: null,
};

interface UseInteractionsOptions {
    canCreate: boolean;
    onAuthenticationRequired: () => void;
}

export function useInteractions({
    canCreate,
    onAuthenticationRequired,
}: UseInteractionsOptions) {
    const [state, setState] = useState<InteractionsState>(initialState);

    const recordInteraction = useCallback(
        async (payload: CreateInteractionRequest): Promise<Interaction | null> => {
            if (!canCreate) {
                onAuthenticationRequired();
                return null;
            }

            setState((current) => ({ ...current, status: 'loading', error: null }));

            try {
                const interaction = await interactionService.createInteraction(payload);
                setState((current) => ({
                    interactions: [...current.interactions, interaction],
                    status: 'success',
                    error: null,
                }));
                return interaction;
            } catch (error) {
                setState((current) => ({
                    ...current,
                    status: 'error',
                    error: getErrorMessage(error, 'Unable to record the interaction.'),
                }));
                return null;
            }
        },
        [canCreate, onAuthenticationRequired],
    );

    const clearInteractions = useCallback((): void => {
        setState(initialState);
    }, []);

    return {
        ...state,
        isSubmitting: state.status === 'loading',
        recordInteraction,
        clearInteractions,
    };
}
