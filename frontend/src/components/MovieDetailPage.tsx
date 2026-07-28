import { useCallback } from 'react';
import { useSimulatedPlayback } from '../features/movies/useSimulatedPlayback';
import type { Movie } from '../types/api';

interface MovieDetailPageProps {
    movie: Movie | null;
    isLoading: boolean;
    error: string | null;
    onBack: () => void;
    onWatch: (movieId: string) => boolean;
    onRate: (movieId: string, rating: number) => boolean;
}

interface DetailListProps {
    label: string;
    values: string[];
}

const fallbackPoster = `data:image/svg+xml,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="1200" viewBox="0 0 900 1200">
        <defs>
            <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#27272a"/>
                <stop offset="1" stop-color="#09090b"/>
            </linearGradient>
        </defs>
        <rect width="900" height="1200" fill="url(#background)"/>
        <circle cx="450" cy="520" r="110" fill="#dc2626" opacity=".8"/>
        <polygon points="420,455 420,585 530,520" fill="white"/>
        <text x="450" y="750" fill="#d4d4d8" font-family="sans-serif" font-size="42" text-anchor="middle">
            Poster unavailable
        </text>
    </svg>
`)}`;

function formatRuntime(runtime: number | null): string {
    if (!runtime || runtime <= 0) {
        return 'Runtime unavailable';
    }
    const hours = Math.floor(runtime / 60);
    const minutes = runtime % 60;
    if (hours === 0) {
        return `${minutes}m`;
    }
    return `${hours}h ${minutes.toString().padStart(2, '0')}m`;
}

function formatClock(totalSeconds: number): string {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds
            .toString()
            .padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function DetailList({ label, values }: DetailListProps) {
    return (
        <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
                {label}
            </dt>
            <dd className="mt-2 text-sm leading-6 text-zinc-200">
                {values.length > 0 ? values.join(', ') : 'Not available'}
            </dd>
        </div>
    );
}

function MovieDetailPage({
    movie,
    isLoading,
    error,
    onBack,
    onWatch,
    onRate,
}: MovieDetailPageProps) {
    const playMovie = useCallback(
        () => (movie ? onWatch(movie.movie_id) : false),
        [movie, onWatch],
    );
    const playback = useSimulatedPlayback(movie?.runtime ?? null, playMovie);

    if (isLoading) {
        return (
            <main className="min-h-screen bg-[#05070b] px-4 py-8 text-white">
                <div className="mx-auto max-w-7xl animate-pulse">
                    <div className="h-10 w-32 rounded-full bg-zinc-800" />
                    <div className="mt-8 aspect-video rounded-3xl bg-zinc-900" />
                    <div className="mt-8 h-12 w-2/3 rounded bg-zinc-900" />
                    <div className="mt-4 h-24 rounded bg-zinc-900" />
                </div>
            </main>
        );
    }

    if (error || !movie) {
        return (
            <main className="grid min-h-screen place-items-center bg-[#05070b] px-4 text-white">
                <section className="max-w-lg rounded-3xl border border-red-500/30 bg-red-500/10 p-8 text-center">
                    <p className="text-sm font-semibold uppercase tracking-[0.25em] text-red-300">
                        Movie unavailable
                    </p>
                    <h1 className="mt-3 text-3xl font-semibold">
                        We could not load this title.
                    </h1>
                    <p className="mt-4 text-zinc-300">
                        {error || 'The requested movie does not exist.'}
                    </p>
                    <button
                        type="button"
                        onClick={onBack}
                        className="mt-6 rounded-full bg-white px-6 py-3 text-sm font-semibold text-zinc-950"
                    >
                        Back to movies
                    </button>
                </section>
            </main>
        );
    }

    const poster = movie.poster_path || fallbackPoster;
    const runtime = formatRuntime(movie.runtime);

    return (
        <main className="min-h-screen bg-[#05070b] text-white">
            <section className="relative isolate overflow-hidden border-b border-white/10">
                <img
                    src={poster}
                    alt=""
                    aria-hidden="true"
                    className="absolute inset-0 h-full w-full scale-105 object-cover opacity-20 blur-2xl"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/45 via-[#05070b]/85 to-[#05070b]" />

                <div className="relative mx-auto max-w-7xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
                    <button
                        type="button"
                        onClick={onBack}
                        className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/30 px-4 py-2 text-sm font-medium text-zinc-200 backdrop-blur transition hover:bg-white/10"
                    >
                        <span aria-hidden="true">←</span>
                        Back to movies
                    </button>

                    <div className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black shadow-2xl shadow-black/60">
                        <div className="relative aspect-video">
                            <img
                                src={poster}
                                alt={`${movie.title} poster`}
                                className="h-full w-full object-cover"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-black/10" />
                            <div className="absolute inset-0 grid place-items-center">
                                <button
                                    type="button"
                                    onClick={playback.togglePlayback}
                                    disabled={playback.durationSeconds === 0}
                                    aria-label={
                                        playback.isPlaying
                                            ? 'Pause simulated playback'
                                            : 'Play simulated playback'
                                    }
                                    className="grid h-20 w-20 place-items-center rounded-full border border-white/30 bg-black/55 text-white shadow-xl backdrop-blur transition hover:scale-105 hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                    {playback.isPlaying ? (
                                        <svg
                                            viewBox="0 0 24 24"
                                            className="h-8 w-8 fill-current"
                                            aria-hidden="true"
                                        >
                                            <rect x="6" y="5" width="4" height="14" rx="1" />
                                            <rect x="14" y="5" width="4" height="14" rx="1" />
                                        </svg>
                                    ) : (
                                        <svg
                                            viewBox="0 0 24 24"
                                            className="ml-1 h-9 w-9 fill-current"
                                            aria-hidden="true"
                                        >
                                            <path d="M7 4.8v14.4c0 .8.9 1.3 1.6.8l10.1-7.2a1 1 0 0 0 0-1.6L8.6 4C7.9 3.5 7 4 7 4.8Z" />
                                        </svg>
                                    )}
                                </button>
                            </div>

                            <div className="absolute inset-x-0 bottom-0 p-4 sm:p-6">
                                <div className="mb-2 flex items-center justify-between text-xs font-medium text-zinc-200 sm:text-sm">
                                    <span>
                                        {formatClock(playback.elapsedSeconds)} /{' '}
                                        {formatClock(playback.durationSeconds)}
                                    </span>
                                    <span>{runtime}</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max={Math.max(playback.durationSeconds, 1)}
                                    value={playback.elapsedSeconds}
                                    disabled={playback.durationSeconds === 0}
                                    onChange={(event) =>
                                        playback.seek(Number(event.target.value))
                                    }
                                    aria-label="Simulated playback progress"
                                    aria-valuetext={`${Math.round(playback.progress)} percent`}
                                    className="h-1.5 w-full cursor-pointer accent-red-600 disabled:cursor-not-allowed"
                                />
                            </div>
                        </div>
                    </div>
                    <p className="mt-3 text-center text-xs uppercase tracking-[0.22em] text-zinc-500">
                        Simulated playback using poster artwork — no video file
                    </p>
                </div>
            </section>

            <section className="mx-auto grid max-w-7xl gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)] lg:px-8 lg:py-14">
                <div>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-zinc-300">
                        <span className="rounded-full bg-red-600 px-3 py-1 font-semibold text-white">
                            {movie.vote_average.toFixed(1)} average
                        </span>
                        <span>{movie.release_year ?? 'Year unavailable'}</span>
                        <span>{runtime}</span>
                        <span>{movie.original_language.toUpperCase()}</span>
                    </div>

                    <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                        {movie.title}
                    </h1>
                    <h2 className="mt-8 text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
                        Overview
                    </h2>
                    <p className="mt-3 max-w-4xl text-lg leading-8 text-zinc-300">
                        {movie.overview || 'No overview is available for this movie.'}
                    </p>

                    <h2 className="mt-8 text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
                        Genres
                    </h2>
                    <div className="mt-3 flex flex-wrap gap-2">
                        {movie.genres.length > 0 ? (
                            movie.genres.map((genre) => (
                                <span
                                    key={genre}
                                    className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-zinc-200"
                                >
                                    {genre}
                                </span>
                            ))
                        ) : (
                            <span className="text-sm text-zinc-500">
                                Genres not available
                            </span>
                        )}
                    </div>

                    <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                        <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-5">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                                Release year
                            </p>
                            <p className="mt-2 text-2xl font-semibold">
                                {movie.release_year ?? 'N/A'}
                            </p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-5">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                                Runtime
                            </p>
                            <p className="mt-2 text-2xl font-semibold">{runtime}</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-5">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                                Vote average
                            </p>
                            <p className="mt-2 text-2xl font-semibold">
                                {movie.vote_average.toFixed(1)}
                            </p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-5">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                                Vote count
                            </p>
                            <p className="mt-2 text-2xl font-semibold">
                                {movie.vote_count.toLocaleString()}
                            </p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-5">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                                Popularity
                            </p>
                            <p className="mt-2 text-2xl font-semibold">
                                {movie.popularity.toLocaleString(undefined, {
                                    maximumFractionDigits: 1,
                                })}
                            </p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-5">
                            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                                Original language
                            </p>
                            <p className="mt-2 text-2xl font-semibold uppercase">
                                {movie.original_language || 'N/A'}
                            </p>
                        </div>
                    </div>

                    <button
                        type="button"
                        onClick={() => onRate(movie.movie_id, 5)}
                        className="mt-8 rounded-full border border-white/15 bg-white/5 px-6 py-3 text-sm font-semibold transition hover:border-red-500/50 hover:bg-red-500/10"
                    >
                        Rate 5 stars
                    </button>
                </div>

                <aside className="rounded-3xl border border-white/10 bg-zinc-900/60 p-6">
                    <h2 className="text-lg font-semibold">Movie information</h2>
                    <dl className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-1">
                        <DetailList
                            label="Production companies"
                            values={movie.companies}
                        />
                        <DetailList
                            label="Production countries"
                            values={movie.countries}
                        />
                        <DetailList label="Actors" values={movie.actors} />
                        <DetailList label="Directors" values={movie.directors} />
                        <div>
                            <dt className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
                                Movie ID
                            </dt>
                            <dd className="mt-2 break-all font-mono text-sm text-zinc-300">
                                {movie.movie_id}
                            </dd>
                        </div>
                    </dl>
                </aside>
            </section>
        </main>
    );
}

export default MovieDetailPage;
