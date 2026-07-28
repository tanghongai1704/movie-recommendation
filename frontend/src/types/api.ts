export interface RegisterRequest {
    email: string;
    username: string;
    password: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export type AuthenticatedUserState = 'first_login' | 'returning_user';

export interface UserProfile {
    user_id: string;
    email: string;
    username: string;
    created_at: string;
    onboarding_genres: string[];
    onboarding_completed: boolean;
    last_active_at: string;
    user_state: AuthenticatedUserState;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    user: UserProfile;
}

export interface UpdateProfileRequest {
    email?: string;
    username?: string;
}

export interface CompleteOnboardingRequest {
    onboarding_genres: string[];
}

export interface Movie {
    movie_id: string;
    title: string;
    release_year: number | null;
    genres: string[];
    overview: string;
    poster_path: string | null;
    vote_average: number;
    vote_count: number;
    popularity: number;
    runtime: number | null;
    original_language: string;
    companies: string[];
    countries: string[];
    actors: string[];
    directors: string[];
}

export type MovieSortField = 'vote_average' | 'release_year' | 'title';

export interface MovieListParams {
    limit?: number;
    offset?: number;
    genre?: string;
    sort_by?: MovieSortField;
}

export type InteractionType =
    | 'click'
    | 'watch'
    | 'rating'
    | 'reaction'
    | 'share';

export type InteractionAction =
    | 'open_detail'
    | 'start'
    | 'progress'
    | 'complete'
    | 'submit'
    | 'like'
    | 'dislike'
    | 'native_share'
    | 'copy_link';

export interface CreateInteractionRequest {
    interaction_type: InteractionType;
    interaction_action: InteractionAction;
    movie_id: string;
    interaction_value?: number;
    timestamp: string;
    session_id: string;
}

export type CreateInteractionInput = Omit<
    CreateInteractionRequest,
    'session_id' | 'timestamp'
>;

export interface Interaction {
    user_id: string;
    interaction_key: string;
    event_id: string;
    movie_id: string;
    interaction_type: InteractionType;
    interaction_action: InteractionAction;
    interaction_value: number | null;
    timestamp: string;
    session_id: string;
}

export interface RecommendationItem extends Movie {
    score: number | null;
    reason_code: string | null;
}

export interface RecommendationResponse {
    user_id: string;
    recommendations: RecommendationItem[];
}

export interface RecommendationParams {
    limit?: number;
    offset?: number;
    context?: string;
}

export interface ApiErrorResponse {
    error?: string;
    detail?: string | Array<{ loc: Array<string | number>; msg: string; type: string }>;
}
