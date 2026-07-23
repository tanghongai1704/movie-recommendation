const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

export async function fetchMovies() {
    const token = 'dummy-token-for-demo';
    const response = await fetch(`${API_BASE_URL}/movies`, {
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error('Unable to load movies from the API.');
    }

    return response.json();
}
