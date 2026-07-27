interface OnboardingPageProps {
    username: string;
    onComplete: () => void;
    onLogout: () => void;
}

function OnboardingPage({ username, onComplete, onLogout }: OnboardingPageProps) {
    return (
        <main className="grid min-h-screen place-items-center bg-[#05070b] px-4 text-white">
            <section className="w-full max-w-2xl rounded-3xl border border-white/10 bg-zinc-900/80 p-8 text-center shadow-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-400">
                    First-time setup
                </p>
                <h1 className="mt-3 text-4xl font-semibold">Welcome, {username}</h1>
                <p className="mx-auto mt-4 max-w-lg leading-7 text-zinc-300">
                    Complete onboarding to unlock watching, ratings, and personalized recommendations.
                </p>

                <div className="mt-8 grid gap-4 text-left sm:grid-cols-3">
                    {['Pick favorite genres', 'Rate a few movies', 'Get smarter recommendations'].map((step) => (
                        <div key={step} className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-zinc-300">
                            {step}
                        </div>
                    ))}
                </div>

                <button
                    onClick={onComplete}
                    className="mt-8 rounded-xl bg-red-600 px-8 py-3 font-semibold transition hover:bg-red-500"
                >
                    Complete onboarding
                </button>
                <button
                    onClick={onLogout}
                    className="ml-3 mt-4 rounded-xl border border-white/10 px-6 py-3 text-sm text-zinc-300 transition hover:bg-white/5"
                >
                    Sign out
                </button>
            </section>
        </main>
    );
}

export default OnboardingPage;
