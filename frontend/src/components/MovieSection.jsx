function MovieSection({ title, movies }) {
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
                        key={movie.title}
                        className="group min-w-[200px] flex-1 overflow-hidden rounded-2xl border border-white/10 bg-zinc-900 shadow-lg shadow-black/20 transition duration-300 hover:-translate-y-1 hover:border-red-500/40"
                    >
                        <img
                            src={movie.image}
                            alt={movie.title}
                            className="h-56 w-full object-cover transition duration-300 group-hover:scale-105"
                        />
                        <div className="p-4">
                            <div className="flex items-center justify-between">
                                <h3 className="truncate text-sm font-semibold text-white">{movie.title}</h3>
                                <span className="rounded-full bg-red-600/15 px-2 py-1 text-[11px] font-semibold text-red-300">
                                    {movie.year}
                                </span>
                            </div>
                            <p className="mt-2 text-sm text-zinc-400">Award-winning drama • 4K</p>
                        </div>
                    </article>
                ))}
            </div>
        </section>
    );
}

export default MovieSection;
