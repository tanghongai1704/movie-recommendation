import { useState } from 'react';
import type { Movie } from '../types/api';

interface MovieSectionProps {
    title: string;
    movies: Movie[];
    fallbackImage: string;
    onMovieClick: (movieId: string) => void;
}

const MOVIES_PER_PAGE = 20;

function MovieSection({
    title,
    movies,
    fallbackImage,
    onMovieClick,
}: MovieSectionProps) {
    const [visibleMovieCount, setVisibleMovieCount] = useState(MOVIES_PER_PAGE);
    const visibleMovies = movies.slice(0, visibleMovieCount);
    const hasMoreMovies = visibleMovieCount < movies.length;

    return (
        <section className="mb-8">
            <div className="mb-5 flex items-end justify-between gap-4">
                <div>
                    <h2 className="text-xl font-semibold text-white">{title}</h2>
                    <p className="mt-1 text-sm text-zinc-500">
                        Select a movie to open its viewing page.
                    </p>
                </div>
                <p className="text-sm text-zinc-500" aria-live="polite">
                    {visibleMovies.length} of {movies.length}
                </p>
            </div>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {visibleMovies.map((movie) => (
                    <article
                        key={movie.movie_id}
                        className="group relative overflow-hidden rounded-2xl border border-white/10 bg-zinc-900 text-left shadow-lg shadow-black/20 transition duration-300 hover:-translate-y-1 hover:border-red-500/50 focus-within:outline focus-within:outline-2 focus-within:outline-offset-4 focus-within:outline-red-500"
                    >
                        <button
                            type="button"
                            onClick={() => onMovieClick(movie.movie_id)}
                            className="absolute inset-0 z-10"
                            aria-label={`Open viewing page for ${movie.title}`}
                        />
                        <div className="aspect-[2/3] overflow-hidden bg-zinc-950">
                            <img
                                src={movie.poster_path || fallbackImage}
                                alt={movie.title}
                                loading="lazy"
                                onError={(event) => {
                                    event.currentTarget.src = fallbackImage;
                                }}
                                className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                            />
                        </div>
                        <div className="p-4">
                            <div className="flex items-start justify-between gap-3">
                                <h3 className="line-clamp-2 text-sm font-semibold leading-5 text-white">
                                    {movie.title}
                                </h3>
                                <span className="rounded-full bg-red-600/15 px-2 py-1 text-[11px] font-semibold text-red-300">
                                    {movie.release_year || 'TBA'}
                                </span>
                            </div>
                            <p className="mt-2 truncate text-sm text-zinc-400">
                                {movie.genres.join(' · ') || 'Movie'} · ★ {movie.vote_average.toFixed(1)}
                            </p>
                        </div>
                    </article>
                ))}
            </div>

            {hasMoreMovies && (
                <div className="mt-10 flex justify-center">
                    <button
                        type="button"
                        onClick={() =>
                            setVisibleMovieCount((current) =>
                                Math.min(current + MOVIES_PER_PAGE, movies.length),
                            )
                        }
                        className="rounded-full border border-white/20 bg-white/5 px-8 py-3 text-sm font-semibold text-white transition hover:border-red-500/60 hover:bg-red-600"
                    >
                        More film
                    </button>
                </div>
            )}
        </section>
    );
}

export default MovieSection;
