import { useState } from 'react';

const availableGenres = [
    'Action',
    'Comedy',
    'Drama',
    'Fantasy',
    'Horror',
    'Romance',
    'Science Fiction',
    'Thriller',
];
const maximumGenres = 3;

interface OnboardingPageProps {
    username: string;
    isSubmitting: boolean;
    error: string | null;
    onComplete: (genres: string[]) => Promise<unknown>;
    onLogout: () => Promise<void>;
}

function OnboardingPage({
    username,
    isSubmitting,
    error,
    onComplete,
    onLogout,
}: OnboardingPageProps) {
    const [selectedGenres, setSelectedGenres] = useState<string[]>([]);

    const toggleGenre = (genre: string): void => {
        setSelectedGenres((current) =>
            current.includes(genre)
                ? current.filter((item) => item !== genre)
                : current.length < maximumGenres
                  ? [...current, genre]
                  : current,
        );
    };

    return (
        <main className="grid min-h-screen place-items-center bg-[#05070b] px-4 text-white">
            <section className="w-full max-w-2xl rounded-3xl border border-white/10 bg-zinc-900/80 p-8 text-center shadow-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-400">
                    First-time setup
                </p>
                <h1 className="mt-3 text-4xl font-semibold">Welcome, {username}</h1>
                <p className="mx-auto mt-4 max-w-lg leading-7 text-zinc-300">
                    Select between one and three genres to unlock personalized
                    recommendations.
                </p>
                <p className="mt-3 text-sm font-medium text-zinc-400">
                    {selectedGenres.length} / {maximumGenres} selected
                </p>

                <div className="mt-8 flex flex-wrap justify-center gap-3">
                    {availableGenres.map((genre) => {
                        const selected = selectedGenres.includes(genre);
                        const selectionLimitReached =
                            selectedGenres.length >= maximumGenres && !selected;
                        return (
                            <button
                                key={genre}
                                type="button"
                                aria-pressed={selected}
                                disabled={selectionLimitReached}
                                onClick={() => toggleGenre(genre)}
                                className={`rounded-full border px-4 py-2 text-sm transition disabled:cursor-not-allowed disabled:opacity-35 ${
                                    selected
                                        ? 'border-red-500 bg-red-500/20 text-red-100'
                                        : 'border-white/10 bg-black/20 text-zinc-300 hover:border-white/30'
                                }`}
                            >
                                {genre}
                            </button>
                        );
                    })}
                </div>

                {error && (
                    <p className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
                        {error}
                    </p>
                )}

                <button
                    onClick={() => void onComplete(selectedGenres)}
                    disabled={selectedGenres.length === 0 || isSubmitting}
                    className="mt-8 rounded-xl bg-red-600 px-8 py-3 font-semibold transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    {isSubmitting ? 'Saving preferences…' : 'Complete onboarding'}
                </button>
                <button
                    onClick={() => void onLogout()}
                    className="ml-3 mt-4 rounded-xl border border-white/10 px-6 py-3 text-sm text-zinc-300 transition hover:bg-white/5"
                >
                    Sign out
                </button>
            </section>
        </main>
    );
}

export default OnboardingPage;
