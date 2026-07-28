import type { FormEvent } from 'react';

interface RegisterPageProps {
    email: string;
    username: string;
    password: string;
    isSubmitting: boolean;
    error: string | null;
    onEmailChange: (value: string) => void;
    onUsernameChange: (value: string) => void;
    onPasswordChange: (value: string) => void;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
    onSignIn: () => void;
    onBrowseAsGuest: () => void;
}

function RegisterPage({
    email,
    username,
    password,
    isSubmitting,
    error,
    onEmailChange,
    onUsernameChange,
    onPasswordChange,
    onSubmit,
    onSignIn,
    onBrowseAsGuest,
}: RegisterPageProps) {
    return (
        <main className="grid min-h-screen place-items-center bg-[#05070b] px-4 py-8 text-white">
            <section className="w-full max-w-md rounded-3xl border border-white/10 bg-zinc-900/80 p-8 shadow-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-400">
                    StreamVerse
                </p>
                <h1 className="mt-3 text-3xl font-semibold">Create your account</h1>
                <p className="mt-2 text-sm text-zinc-400">
                    Register once, select your favorite genres, and unlock personalized recommendations.
                </p>

                <form className="mt-8 space-y-5" onSubmit={onSubmit}>
                    <label className="block text-sm font-medium text-zinc-200">
                        Email
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => onEmailChange(event.target.value)}
                            autoComplete="email"
                            required
                            className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 outline-none transition focus:border-red-500"
                        />
                    </label>
                    <label className="block text-sm font-medium text-zinc-200">
                        Username
                        <input
                            value={username}
                            onChange={(event) => onUsernameChange(event.target.value)}
                            autoComplete="username"
                            minLength={3}
                            required
                            className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 outline-none transition focus:border-red-500"
                        />
                    </label>
                    <label className="block text-sm font-medium text-zinc-200">
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(event) => onPasswordChange(event.target.value)}
                            autoComplete="new-password"
                            minLength={8}
                            required
                            className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 outline-none transition focus:border-red-500"
                        />
                    </label>

                    {error && (
                        <p className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full rounded-xl bg-red-600 px-4 py-3 font-semibold transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {isSubmitting ? 'Creating account…' : 'Create Account'}
                    </button>
                </form>

                <button
                    onClick={onSignIn}
                    className="mt-4 w-full rounded-xl border border-white/10 px-4 py-3 text-sm text-zinc-300 transition hover:bg-white/5"
                >
                    Already registered? Sign in
                </button>
                <button
                    onClick={onBrowseAsGuest}
                    className="mt-3 w-full text-sm font-medium text-zinc-400 transition hover:text-white"
                >
                    Continue browsing as guest
                </button>
            </section>
        </main>
    );
}

export default RegisterPage;
