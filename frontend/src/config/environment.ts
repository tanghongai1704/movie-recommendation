interface FrontendConfiguration {
    apiBaseUrl: string;
    tmdbPosterBaseUrl: string;
}

function requiredHttpUrl(name: string, value: string | undefined): string {
    const normalized = value?.trim().replace(/\/+$/, '');
    if (!normalized) {
        throw new Error(`Missing required frontend environment variable: ${name}`);
    }

    let parsed: URL;
    try {
        parsed = new URL(normalized);
    } catch {
        throw new Error(`${name} must be a valid HTTP(S) URL`);
    }
    if (!['http:', 'https:'].includes(parsed.protocol)) {
        throw new Error(`${name} must use the http or https scheme`);
    }
    return normalized;
}

export const frontendConfig: Readonly<FrontendConfiguration> = Object.freeze({
    apiBaseUrl: requiredHttpUrl('VITE_API_URL', import.meta.env.VITE_API_URL),
    tmdbPosterBaseUrl: requiredHttpUrl(
        'VITE_TMDB_POSTER_BASE_URL',
        import.meta.env.VITE_TMDB_POSTER_BASE_URL,
    ),
});
