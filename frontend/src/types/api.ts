export interface LoginRequest {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface UserProfile {
    user_id: number;
    username: string;
    role: string;
}

export interface Movie {
    id: number;
    title: string;
    genre: string;
    year: number;
    rating: number;
    description: string;
    image_url: string;
}

export type MovieSortField = 'rating' | 'year' | 'title';

export interface MovieListParams {
    limit?: number;
    offset?: number;
    genre?: string;
    sort_by?: MovieSortField;
}

export type InteractionEventType = 'click' | 'watch' | 'rating';

export interface CreateInteractionRequest {
    event_type: InteractionEventType;
    movie_id: number;
    rating?: number;
    metadata?: Record<string, unknown>;
}

export interface Interaction {
    event_id: string;
    user_id: number;
    event_type: InteractionEventType;
    movie_id: number;
    rating?: number;
    created_at: string;
}

export interface RecommendationItem {
    movie_id: number;
    title: string;
    score: number | null;
}

export interface RecommendationResponse {
    user_id: number;
    recommendations: RecommendationItem[];
}

export interface RecommendationParams {
    user_id?: number;
    limit?: number;
    offset?: number;
    context?: string;
}

export interface ApiErrorResponse {
    error?: string;
    detail?: string | Array<{ loc: Array<string | number>; msg: string; type: string }>;
}
