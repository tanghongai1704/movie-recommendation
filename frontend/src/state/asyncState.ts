export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

export function getErrorMessage(error: unknown, fallback: string): string {
    return error instanceof Error ? error.message : fallback;
}
