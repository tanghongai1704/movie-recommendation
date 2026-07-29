import type { AuthUserState } from '../features/auth/useAuth';
import type { Movie } from '../types/api';
import MovieSection from './MovieSection';
import SiteHeader from './SiteHeader';

interface HomePageProps {
    userState: AuthUserState;
    username: string | null;
    movies: Movie[];
    moviesLoading: boolean;
    moviesError: string | null;
    interactionError: string | null;
    onHome: () => void;
    onSignIn: () => void;
    onProfile: () => void;
    onLogout: () => Promise<void>;
    onMovieClick: (movieId: string) => void;
    onWatch: (movieId: string) => void;
    onRate: (movieId: string, rating: number) => Promise<boolean>;
}

const featuredMovie = {
    id: '1',
    title: 'Midnight Horizon',
    year: '2025',
    duration: '2h 08m',
    rating: '8.9',
    category: 'Sci-Fi Thriller',
    description:
        'A brilliant pilot and a rogue AI race through a collapsing city to prevent a global blackout that could erase humanity’s memories.',
    image:
        'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1400&q=80',
};

function HomePage({
    userState,
    username,
    movies,
    moviesLoading,
    moviesError,
    interactionError,
    onHome,
    onSignIn,
    onProfile,
    onLogout,
    onMovieClick,
    onWatch,
    onRate,
}: HomePageProps) {
    const isGuest = userState === 'guest';

    return (
        <div className="min-h-screen bg-[#05070b] text-white">
            <SiteHeader
                userState={userState}
                username={username}
                onHome={onHome}
                onSignIn={onSignIn}
                onProfile={onProfile}
                onLogout={onLogout}
                primaryAction={{
                    label: 'Start Watching',
                    onClick: () => onWatch(featuredMovie.id),
                }}
            />

            <main>
                <section className="relative isolate overflow-hidden border-b border-white/10">
                    <img
                        src={featuredMovie.image}
                        alt={featuredMovie.title}
                        className="absolute inset-0 h-full w-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-r from-[#05070b] via-[#05070b]/85 to-[#05070b]/20" />

                    <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-24 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-32">
                        <div className="max-w-2xl">
                            <p className="mb-4 inline-flex rounded-full border border-red-500/40 bg-red-500/10 px-3 py-1 text-sm font-medium text-red-300">
                                New Release • {featuredMovie.category}
                            </p>
                            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl lg:text-7xl">
                                {featuredMovie.title}
                            </h1>
                            <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-zinc-300">
                                <span className="rounded-full bg-white/10 px-3 py-1">{featuredMovie.year}</span>
                                <span>{featuredMovie.duration}</span>
                                <span>★ {featuredMovie.rating}</span>
                            </div>
                            <p className="mt-6 text-lg leading-8 text-zinc-300 sm:text-xl">
                                {featuredMovie.description}
                            </p>
                            <div className="mt-8 flex flex-wrap gap-4">
                                <button
                                    onClick={() => onWatch(featuredMovie.id)}
                                    className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200"
                                >
                                    ▶ Play Now
                                </button>
                                <button
                                    onClick={() => void onRate(featuredMovie.id, 5)}
                                    className="rounded-full border border-white/20 bg-white/10 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/20"
                                >
                                    ★ Rate 5
                                </button>
                            </div>
                            {isGuest && (
                                <p className="mt-4 text-sm text-zinc-400">
                                    Browse freely. Sign in when you’re ready to watch or rate.
                                </p>
                            )}
                        </div>

                        <div className="rounded-3xl border border-white/10 bg-black/35 p-6 shadow-2xl shadow-black/40 backdrop-blur-md">
                            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-zinc-400">
                                Why you’ll love it
                            </p>
                            <ul className="mt-6 space-y-4 text-sm text-zinc-300">
                                <li className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                    <span className="block font-semibold text-white">Smart recommendations</span>
                                    Personalized picks based on your recent taste.
                                </li>
                                <li className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                    <span className="block font-semibold text-white">Premium originals</span>
                                    Fresh blockbuster films and exclusive series.
                                </li>
                                <li className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                    <span className="block font-semibold text-white">Ultra-fast streaming</span>
                                    Adaptive playback that feels seamless on any device.
                                </li>
                            </ul>
                        </div>
                    </div>
                </section>

                <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
                    <div className="mb-6">
                        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-400">
                            {isGuest ? 'Explore Movies' : 'Your Movie Catalog'}
                        </p>
                        <h2 className="mt-2 text-2xl font-semibold text-white">
                            {isGuest
                                ? 'Browse freely and sign in for protected actions'
                                : 'Your registered account is ready for protected actions'}
                        </h2>
                    </div>

                    {interactionError && (
                        <div className="mb-6 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
                            {interactionError}
                        </div>
                    )}

                    {moviesLoading ? (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {[1, 2, 3].map((item) => (
                                <div key={item} className="animate-pulse rounded-2xl border border-white/10 bg-zinc-900 p-4">
                                    <div className="h-40 rounded-xl bg-zinc-800" />
                                    <div className="mt-4 h-4 w-2/3 rounded bg-zinc-800" />
                                    <div className="mt-2 h-4 w-1/2 rounded bg-zinc-800" />
                                </div>
                            ))}
                        </div>
                    ) : moviesError ? (
                        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-sm text-red-200">
                            {moviesError}
                        </div>
                    ) : (
                        <MovieSection
                            title={isGuest ? 'Popular Now' : 'Movies for you'}
                            movies={movies}
                            fallbackImage={featuredMovie.image}
                            onMovieClick={onMovieClick}
                        />
                    )}
                </section>
            </main>
        </div>
    );
}

export default HomePage;
