import type { Movie } from '../types/api';

interface MovieSectionProps {
    title: string;
    movies: Movie[];
    fallbackImage: string;
    onMovieClick: (movieId: string) => void;
    onWatch: (movieId: string) => void;
    onRate: (movieId: string, rating: number) => void;
}

function MovieSection({
    title,
    movies,
    fallbackImage,
    onMovieClick,
    onWatch,
    onRate,
}: MovieSectionProps) {
    return (
        <section className="mb-8">
            <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">{title}</h2>
                <a href="#" className="text-sm font-medium text-zinc-400 transition hover:text-white">
                    Explore all
                </a>
            </div>

            <div className="flex gap-4 overflow-x-auto pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                {movies.map((movie) => (
                    <article
                        key={movie.movie_id}
                        className="group min-w-[200px] flex-1 overflow-hidden rounded-2xl border border-white/10 bg-zinc-900 shadow-lg shadow-black/20 transition duration-300 hover:-translate-y-1 hover:border-red-500/40"
                    >
                        <button
                            type="button"
                            onClick={() => onMovieClick(movie.movie_id)}
                            className="block w-full overflow-hidden"
                            aria-label={`View details for ${movie.title}`}
                        >
                            <img
                                src={movie.poster_path || fallbackImage}
                                alt={movie.title}
                                className="h-56 w-full object-cover transition duration-300 group-hover:scale-105"
                            />
                        </button>
                        <div className="p-4">
                            <div className="flex items-center justify-between">
                                <h3 className="truncate text-sm font-semibold text-white">{movie.title}</h3>
                                <span className="rounded-full bg-red-600/15 px-2 py-1 text-[11px] font-semibold text-red-300">
                                    {movie.release_year || 'TBA'}
                                </span>
                            </div>
                            <p className="mt-2 truncate text-sm text-zinc-400">
                                {movie.genres.join(' · ') || 'Movie'} · ★ {movie.vote_average.toFixed(1)}
                            </p>
                            <div className="mt-4 flex gap-2">
                                <button
                                    onClick={() => onWatch(movie.movie_id)}
                                    className="flex-1 rounded-lg bg-white px-3 py-2 text-xs font-semibold text-zinc-950"
                                >
                                    Watch
                                </button>
                                <button
                                    onClick={() => onRate(movie.movie_id, 5)}
                                    className="flex-1 rounded-lg border border-white/15 px-3 py-2 text-xs font-semibold text-white"
                                >
                                    ★ Rate
                                </button>
                            </div>
                        </div>
                    </article>
                ))}
            </div>
        </section>
    );
}

export default MovieSection;
