import { useCallback, useState } from 'react';
import type { AuthUserState } from '../features/auth/useAuth';
import { useMovieRating } from '../features/interactions/useMovieRating';
import {
    useMovieReaction,
    type MovieReaction,
} from '../features/interactions/useMovieReaction';
import { useSimulatedPlayback } from '../features/movies/useSimulatedPlayback';
import type { Movie } from '../types/api';
import SiteHeader from './SiteHeader';

interface MovieDetailPageProps {
    movie: Movie | null;
    isLoading: boolean;
    error: string | null;
    interactionError: string | null;
    userState: AuthUserState;
    username: string | null;
    onBack: () => void;
    onSignIn: () => void;
    onProfile: () => void;
    onLogout: () => Promise<void>;
    onWatch: (movieId: string) => boolean;
    onWatchProgress: (movieId: string, progress: number) => void;
    onRate: (movieId: string, rating: number) => Promise<boolean>;
    onClearRating: (movieId: string) => Promise<boolean>;
    onReact: (
        movieId: string,
        reaction: MovieReaction | null,
    ) => Promise<boolean>;
    onShare: (movieId: string) => boolean;
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

interface HalfStarRatingProps {
    score: number;
    onRate: (rating: number) => void;
    disabled?: boolean;
}

const ratingSteps = Array.from({ length: 10 }, (_, index) => (index + 1) / 2);

function HalfStarRating({
    score,
    onRate,
    disabled = false,
}: HalfStarRatingProps) {
    const normalizedScore = Math.min(Math.max(score, 0), 5);
    const [previewScore, setPreviewScore] = useState<number | null>(null);
    const displayedScore = previewScore ?? normalizedScore;
    const fillPercentage = (displayedScore / 5) * 100;

    return (
        <div
            className="relative h-9 w-[180px]"
            role="group"
            aria-label={`Current rating: ${normalizedScore.toFixed(1)} out of 5`}
        >
            <div className="flex" aria-hidden="true">
                {[1, 2, 3, 4, 5].map((star) => (
                    <svg
                        key={star}
                        viewBox="0 0 24 24"
                        className="h-9 w-9 shrink-0 fill-zinc-600"
                    >
                        <path d="m12 2.2 3 6.1 6.7 1-4.9 4.7 1.2 6.7-6-3.1-6 3.1 1.2-6.7-4.9-4.7 6.7-1 3-6.1Z" />
                    </svg>
                ))}
            </div>
            <span
                className="pointer-events-none absolute inset-y-0 left-0 overflow-hidden"
                style={{ width: `${fillPercentage}%` }}
                aria-hidden="true"
            >
                <span className="flex w-[180px]">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <svg
                            key={star}
                            viewBox="0 0 24 24"
                            className="h-9 w-9 shrink-0 fill-amber-400"
                        >
                            <path d="m12 2.2 3 6.1 6.7 1-4.9 4.7 1.2 6.7-6-3.1-6 3.1 1.2-6.7-4.9-4.7 6.7-1 3-6.1Z" />
                        </svg>
                    ))}
                </span>
            </span>
            <div
                className="absolute inset-0 grid grid-cols-10"
                onMouseLeave={() => setPreviewScore(null)}
            >
                {ratingSteps.map((rating) => (
                    <button
                        key={rating}
                        type="button"
                        onClick={() => onRate(rating)}
                        onMouseEnter={() => setPreviewScore(rating)}
                        onFocus={() => setPreviewScore(rating)}
                        onBlur={() => setPreviewScore(null)}
                        disabled={disabled}
                        className="h-9 focus-visible:z-10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-red-500 disabled:cursor-wait"
                        aria-label={`Rate ${rating.toFixed(1)} stars`}
                        title={`${rating.toFixed(1)} stars`}
                    />
                ))}
            </div>
        </div>
    );
}

function MovieRatingSummary({ movie }: { movie: Movie }) {
    const fiveStarScore = Math.min(Math.max(movie.vote_average / 2, 0), 5);

    return (
        <div
            className="mt-3 flex flex-wrap items-center gap-2 text-zinc-300"
            aria-label={`${fiveStarScore.toFixed(1)} out of 5 from ${movie.vote_count.toLocaleString()} votes`}
        >
            <span className="text-2xl font-bold text-white">
                {fiveStarScore.toFixed(1)}
            </span>
            <span className="text-xl text-amber-400" aria-hidden="true">
                ★
            </span>
            <span className="text-sm uppercase text-zinc-400">
                ({movie.vote_count.toLocaleString()} votes)
            </span>
        </div>
    );
}

interface MovieEngagementProps {
    movie: Movie;
    userRating: number | null;
    isRatingLoading: boolean;
    onRate: (rating: number) => Promise<boolean>;
    onClearRating: () => Promise<boolean>;
    selectedReaction: MovieReaction | null;
    isReactionLoading: boolean;
    onReact: (reaction: MovieReaction) => Promise<boolean>;
    onShare: (movieId: string) => boolean;
}

function MovieEngagement({
    movie,
    userRating,
    isRatingLoading,
    onRate,
    onClearRating,
    selectedReaction,
    isReactionLoading,
    onReact,
    onShare,
}: MovieEngagementProps) {
    const selectedScore = Math.min(Math.max(userRating ?? 0, 0), 5);

    return (
        <section
            className="mt-8 flex flex-col gap-6 rounded-2xl border border-white/15 bg-[#151515] px-5 py-5 shadow-xl shadow-black/30 sm:px-7 lg:flex-row lg:items-center"
            aria-label="Movie rating and actions"
        >
            <div className="min-w-fit">
                <div className="flex items-center justify-between gap-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">
                        Your rating
                    </p>
                    <span className="text-xs text-zinc-500" aria-live="polite">
                        {userRating === null
                            ? 'Not rated'
                            : `${userRating.toFixed(1)} / 5`}
                    </span>
                </div>
                <div className="mt-2">
                    <HalfStarRating
                        score={selectedScore}
                        onRate={(rating) => void onRate(rating)}
                        disabled={isRatingLoading}
                    />
                </div>
                {userRating !== null && (
                    <button
                        type="button"
                        onClick={() => void onClearRating()}
                        disabled={isRatingLoading}
                        className="mt-2 text-xs font-semibold text-zinc-400 underline-offset-4 transition hover:text-white hover:underline disabled:cursor-wait disabled:opacity-50"
                    >
                        Clear rating
                    </button>
                )}
            </div>

            <div className="hidden h-20 w-px bg-white/15 lg:block" aria-hidden="true" />

            <div className="flex flex-wrap items-center gap-3 sm:gap-5">
                <button
                    type="button"
                    onClick={() => void onReact('like')}
                    disabled={isReactionLoading}
                    className={`grid h-14 w-14 place-items-center rounded-full border transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-wait disabled:opacity-60 ${
                        selectedReaction === 'like'
                            ? 'border-red-500 bg-red-600/15 text-red-500 hover:bg-red-600/25 focus-visible:outline-red-500'
                            : 'border-transparent text-zinc-300 hover:border-white/20 hover:bg-white/5 hover:text-white focus-visible:outline-white'
                    }`}
                    aria-label={
                        selectedReaction === 'like'
                            ? 'Remove like'
                            : 'Like this movie'
                    }
                    aria-pressed={selectedReaction === 'like'}
                    title={selectedReaction === 'like' ? 'Remove like' : 'Like'}
                >
                    <svg
                        viewBox="0 0 24 24"
                        className="h-7 w-7 fill-none stroke-current stroke-2"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M8.2 20H4.5A1.5 1.5 0 0 1 3 18.5v-7A1.5 1.5 0 0 1 4.5 10h3.7v10Zm2 0V9.2l3.1-6.1c.3-.6 1.1-.9 1.7-.5.4.2.6.6.6 1v4.1h3.1c1.5 0 2.6 1.4 2.3 2.8l-1.7 7.4c-.3 1.2-1.3 2.1-2.6 2.1h-6.5Z"
                        />
                    </svg>
                </button>
                <button
                    type="button"
                    onClick={() => void onReact('dislike')}
                    disabled={isReactionLoading}
                    className={`grid h-14 w-14 place-items-center rounded-full border transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-wait disabled:opacity-60 ${
                        selectedReaction === 'dislike'
                            ? 'border-red-500 bg-red-600/15 text-red-500 hover:bg-red-600/25 focus-visible:outline-red-500'
                            : 'border-transparent text-zinc-300 hover:border-white/20 hover:bg-white/5 hover:text-white focus-visible:outline-white'
                    }`}
                    aria-label={
                        selectedReaction === 'dislike'
                            ? 'Remove dislike'
                            : 'Dislike this movie'
                    }
                    aria-pressed={selectedReaction === 'dislike'}
                    title={
                        selectedReaction === 'dislike'
                            ? 'Remove dislike'
                            : 'Dislike'
                    }
                >
                    <svg
                        viewBox="0 0 24 24"
                        className="h-7 w-7 rotate-180 fill-none stroke-current stroke-2"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M8.2 20H4.5A1.5 1.5 0 0 1 3 18.5v-7A1.5 1.5 0 0 1 4.5 10h3.7v10Zm2 0V9.2l3.1-6.1c.3-.6 1.1-.9 1.7-.5.4.2.6.6.6 1v4.1h3.1c1.5 0 2.6 1.4 2.3 2.8l-1.7 7.4c-.3 1.2-1.3 2.1-2.6 2.1h-6.5Z"
                        />
                    </svg>
                </button>
                <button
                    type="button"
                    onClick={() => onShare(movie.movie_id)}
                    className="inline-flex h-14 items-center gap-3 rounded-full px-3 text-sm font-semibold uppercase text-zinc-100 transition hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                >
                    <svg
                        viewBox="0 0 24 24"
                        className="h-7 w-7 fill-none stroke-current stroke-2"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="m14 5 5 5-5 5M19 10h-7a7 7 0 0 0-7 7v2"
                        />
                    </svg>
                    Sharing
                </button>
            </div>
        </section>
    );
}

function MovieDetailPage({
    movie,
    isLoading,
    error,
    interactionError,
    userState,
    username,
    onBack,
    onSignIn,
    onProfile,
    onLogout,
    onWatch,
    onWatchProgress,
    onRate,
    onClearRating,
    onReact,
    onShare,
}: MovieDetailPageProps) {
    const playMovie = useCallback(
        () => (movie ? onWatch(movie.movie_id) : false),
        [movie, onWatch],
    );
    const recordWatchMilestone = useCallback(
        (progress: number) => {
            if (movie) {
                onWatchProgress(movie.movie_id, progress);
            }
        },
        [movie, onWatchProgress],
    );
    const playback = useSimulatedPlayback(
        movie?.runtime ?? null,
        playMovie,
        recordWatchMilestone,
        movie?.movie_id ?? null,
    );
    const movieRating = useMovieRating({
        movieId: movie?.movie_id ?? null,
        canLoadRating: userState !== 'guest',
        onRate,
        onClear: onClearRating,
    });
    const movieReaction = useMovieReaction({
        movieId: movie?.movie_id ?? null,
        canLoadReaction: userState !== 'guest',
        onReact,
    });

    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#05070b] text-white">
                <SiteHeader
                    userState={userState}
                    username={username}
                    onHome={onBack}
                    onSignIn={onSignIn}
                    onProfile={onProfile}
                    onLogout={onLogout}
                />
                <main className="px-4 py-8">
                    <div className="mx-auto max-w-7xl animate-pulse">
                        <div className="h-10 w-32 rounded-full bg-zinc-800" />
                        <div className="mt-8 aspect-video rounded-3xl bg-zinc-900" />
                        <div className="mt-8 h-12 w-2/3 rounded bg-zinc-900" />
                        <div className="mt-4 h-24 rounded bg-zinc-900" />
                    </div>
                </main>
            </div>
        );
    }

    if (error || !movie) {
        return (
            <div className="min-h-screen bg-[#05070b] text-white">
                <SiteHeader
                    userState={userState}
                    username={username}
                    onHome={onBack}
                    onSignIn={onSignIn}
                    onProfile={onProfile}
                    onLogout={onLogout}
                />
                <main className="grid min-h-[calc(100vh-73px)] place-items-center px-4">
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
            </div>
        );
    }

    const poster = movie.poster_path || fallbackPoster;
    const runtime = formatRuntime(movie.runtime);

    return (
        <div className="min-h-screen bg-[#05070b] text-white">
            <SiteHeader
                userState={userState}
                username={username}
                onHome={onBack}
                onSignIn={onSignIn}
                onProfile={onProfile}
                onLogout={onLogout}
                primaryAction={{
                    label: playback.isPlaying ? 'Pause' : 'Start Watching',
                    onClick: playback.togglePlayback,
                }}
            />
            <main>
            <section className="relative isolate overflow-hidden border-b border-white/10">
                <img
                    src={poster}
                    alt=""
                    aria-hidden="true"
                    onError={(event) => {
                        event.currentTarget.src = fallbackPoster;
                    }}
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
                                onError={(event) => {
                                    event.currentTarget.src = fallbackPoster;
                                }}
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
                        <span>{movie.release_year ?? 'Year unavailable'}</span>
                        <span>{runtime}</span>
                        <span>{movie.original_language.toUpperCase()}</span>
                    </div>

                    <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                        {movie.title}
                    </h1>

                    <MovieRatingSummary movie={movie} />

                    <h2 className="mt-8 text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500">
                        Overview
                    </h2>
                    <p className="mt-3 max-w-4xl text-lg leading-8 text-zinc-300">
                        {movie.overview || 'No overview is available for this movie.'}
                    </p>

                    <MovieEngagement
                        movie={movie}
                        userRating={movieRating.rating}
                        isRatingLoading={movieRating.isLoading}
                        onRate={movieRating.submitRating}
                        onClearRating={movieRating.clearRating}
                        selectedReaction={movieReaction.reaction}
                        isReactionLoading={movieReaction.isSubmitting}
                        onReact={movieReaction.submitReaction}
                        onShare={onShare}
                    />

                    {(interactionError ||
                        movieRating.error ||
                        movieReaction.error) && (
                        <p className="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
                            {interactionError ||
                                movieRating.error ||
                                movieReaction.error}
                        </p>
                    )}

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

                    <div className="mt-8 grid gap-4 sm:grid-cols-3">
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
                                Original language
                            </p>
                            <p className="mt-2 text-2xl font-semibold uppercase">
                                {movie.original_language || 'N/A'}
                            </p>
                        </div>
                    </div>
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
                    </dl>
                </aside>
            </section>
            </main>
        </div>
    );
}

export default MovieDetailPage;
