import MovieSection from './components/MovieSection';
import { useMovies } from './features/movies/useMovies';

const featuredMovie = {
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

function App() {
    const { movies, isLoading, error } = useMovies();

    return (
        <div className="min-h-screen bg-[#05070b] text-white">
            <header className="sticky top-0 z-20 border-b border-white/10 bg-[#05070b]/90 backdrop-blur">
                <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-6">
                        <div className="text-2xl font-black tracking-[0.35em] text-red-600">
                            STREAMVERSE
                        </div>
                        <nav className="hidden items-center gap-4 text-sm font-medium text-zinc-300 md:flex">
                            <a href="#" className="transition hover:text-white">Home</a>
                            <a href="#" className="transition hover:text-white">Series</a>
                            <a href="#" className="transition hover:text-white">Films</a>
                            <a href="#" className="transition hover:text-white">New &amp; Popular</a>
                        </nav>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:border-white/40 hover:bg-white/5">
                            Sign In
                        </button>
                        <button className="rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500">
                            Start Watching
                        </button>
                    </div>
                </div>
            </header>

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
                                <button className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200">
                                    ▶ Play Now
                                </button>
                                <button className="rounded-full border border-white/20 bg-white/10 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/20">
                                    + My List
                                </button>
                            </div>
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
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-400">
                                Recommended For You
                            </p>
                            <h2 className="mt-2 text-2xl font-semibold text-white">
                                Curated from the backend API
                            </h2>
                        </div>
                    </div>

                    {isLoading ? (
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {[1, 2, 3].map((item) => (
                                <div key={item} className="animate-pulse rounded-2xl border border-white/10 bg-zinc-900 p-4">
                                    <div className="h-40 rounded-xl bg-zinc-800" />
                                    <div className="mt-4 h-4 w-2/3 rounded bg-zinc-800" />
                                    <div className="mt-2 h-4 w-1/2 rounded bg-zinc-800" />
                                </div>
                            ))}
                        </div>
                    ) : error ? (
                        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-sm text-red-200">
                            {error}
                        </div>
                    ) : (
                        <MovieSection
                            title="Recommended For You"
                            movies={movies}
                            fallbackImage={featuredMovie.image}
                        />
                    )}
                </section>
            </main>
        </div>
    );
}

export default App;
