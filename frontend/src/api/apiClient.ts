import type { ApiErrorResponse } from '../types/api';

type QueryValue = string | number | boolean | null | undefined;
type QueryParams = Record<string, QueryValue>;

interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
    body?: unknown;
    query?: QueryParams;
    requiresAuth?: boolean;
    allowGuest?: boolean;
}

const API_BASE_URL = (
    import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'
).replace(/\/+$/, '');
const TOKEN_STORAGE_KEY = 'movie-recommendation.access-token';
const DEFAULT_DEMO_TOKEN = import.meta.env.VITE_API_TOKEN || 'dummy-token-for-demo';

export class ApiError extends Error {
    constructor(
        message: string,
        public readonly status: number,
        public readonly payload?: ApiErrorResponse,
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

class ApiClient {
    private accessToken: string | null = window.localStorage.getItem(TOKEN_STORAGE_KEY);

    hasAuthenticatedSession(): boolean {
        return this.accessToken !== null;
    }

    setAccessToken(token: string): void {
        this.accessToken = token;
        window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    }

    clearAccessToken(): void {
        this.accessToken = null;
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }

    get<TResponse>(
        path: string,
        query?: QueryParams,
        options?: Omit<ApiRequestOptions, 'body' | 'query' | 'method'>,
    ): Promise<TResponse> {
        return this.request<TResponse>(path, { ...options, method: 'GET', query });
    }

    post<TResponse, TBody = unknown>(
        path: string,
        body?: TBody,
        options?: Omit<ApiRequestOptions, 'body' | 'method'>,
    ): Promise<TResponse> {
        return this.request<TResponse>(path, { ...options, method: 'POST', body });
    }

    put<TResponse, TBody = unknown>(
        path: string,
        body?: TBody,
        options?: Omit<ApiRequestOptions, 'body' | 'method'>,
    ): Promise<TResponse> {
        return this.request<TResponse>(path, { ...options, method: 'PUT', body });
    }

    patch<TResponse, TBody = unknown>(
        path: string,
        body?: TBody,
        options?: Omit<ApiRequestOptions, 'body' | 'method'>,
    ): Promise<TResponse> {
        return this.request<TResponse>(path, { ...options, method: 'PATCH', body });
    }

    delete<TResponse>(
        path: string,
        options?: Omit<ApiRequestOptions, 'body' | 'method'>,
    ): Promise<TResponse> {
        return this.request<TResponse>(path, { ...options, method: 'DELETE' });
    }

    private async request<TResponse>(
        path: string,
        {
            body,
            query,
            requiresAuth = true,
            allowGuest = false,
            headers,
            ...init
        }: ApiRequestOptions,
    ): Promise<TResponse> {
        const requestHeaders = new Headers(headers);
        requestHeaders.set('Accept', 'application/json');

        if (body !== undefined) {
            requestHeaders.set('Content-Type', 'application/json');
        }

        if (requiresAuth) {
            const requestToken = this.accessToken || (allowGuest ? DEFAULT_DEMO_TOKEN : null);
            if (!requestToken) {
                throw new ApiError('Authentication is required for this action.', 401);
            }
            requestHeaders.set('Authorization', `Bearer ${requestToken}`);
        }

        const response = await fetch(this.buildUrl(path, query), {
            ...init,
            headers: requestHeaders,
            body: body === undefined ? undefined : JSON.stringify(body),
        });

        const payload = await this.parseResponse<TResponse>(response);

        if (!response.ok) {
            const errorPayload = payload as ApiErrorResponse | undefined;
            const detail =
                typeof errorPayload?.detail === 'string' ? errorPayload.detail : undefined;
            throw new ApiError(
                errorPayload?.error || detail || `API request failed with status ${response.status}.`,
                response.status,
                errorPayload,
            );
        }

        return payload as TResponse;
    }

    private buildUrl(path: string, query?: QueryParams): string {
        const normalizedPath = path.startsWith('/') ? path : `/${path}`;
        const url = new URL(`${API_BASE_URL}${normalizedPath}`);

        Object.entries(query || {}).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                url.searchParams.set(key, String(value));
            }
        });

        return url.toString();
    }

    private async parseResponse<TResponse>(response: Response): Promise<TResponse | undefined> {
        if (response.status === 204) {
            return undefined;
        }

        const contentType = response.headers.get('content-type');
        if (!contentType?.includes('application/json')) {
            return undefined;
        }

        return response.json() as Promise<TResponse>;
    }
}

export const apiClient = new ApiClient();
