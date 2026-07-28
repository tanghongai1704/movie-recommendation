import { useEffect, useState, type FormEvent } from 'react';
import type { UpdateProfileRequest, UserProfile } from '../types/api';

interface ProfilePageProps {
    user: UserProfile;
    isSubmitting: boolean;
    error: string | null;
    onUpdate: (payload: UpdateProfileRequest) => Promise<UserProfile | null>;
    onBack: () => void;
    onLogout: () => Promise<void>;
}

function ProfilePage({
    user,
    isSubmitting,
    error,
    onUpdate,
    onBack,
    onLogout,
}: ProfilePageProps) {
    const [email, setEmail] = useState(user.email);
    const [username, setUsername] = useState(user.username);

    useEffect(() => {
        setEmail(user.email);
        setUsername(user.username);
    }, [user.email, user.username]);

    const submit = (event: FormEvent<HTMLFormElement>): void => {
        event.preventDefault();
        void onUpdate({ email, username });
    };

    return (
        <main className="grid min-h-screen place-items-center bg-[#05070b] px-4 text-white">
            <section className="w-full max-w-xl rounded-3xl border border-white/10 bg-zinc-900/80 p-8 shadow-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-400">
                    Profile
                </p>
                <h1 className="mt-3 text-3xl font-semibold">Account settings</h1>
                <p className="mt-2 text-sm text-zinc-400">
                    Member since {new Date(user.created_at).toLocaleDateString()}
                </p>

                <form className="mt-8 space-y-5" onSubmit={submit}>
                    <label className="block text-sm font-medium text-zinc-200">
                        Email
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            required
                            className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 outline-none transition focus:border-red-500"
                        />
                    </label>
                    <label className="block text-sm font-medium text-zinc-200">
                        Username
                        <input
                            value={username}
                            onChange={(event) => setUsername(event.target.value)}
                            minLength={3}
                            required
                            className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 outline-none transition focus:border-red-500"
                        />
                    </label>

                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                        <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                            Favorite genres
                        </p>
                        <p className="mt-2 text-sm text-zinc-300">
                            {user.onboarding_genres.join(', ') || 'No genres selected'}
                        </p>
                    </div>

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
                        {isSubmitting ? 'Saving…' : 'Save Profile'}
                    </button>
                </form>

                <div className="mt-4 grid grid-cols-2 gap-3">
                    <button
                        onClick={onBack}
                        className="rounded-xl border border-white/10 px-4 py-3 text-sm text-zinc-300 transition hover:bg-white/5"
                    >
                        Back to home
                    </button>
                    <button
                        onClick={() => void onLogout()}
                        className="rounded-xl border border-red-500/30 px-4 py-3 text-sm text-red-200 transition hover:bg-red-500/10"
                    >
                        Sign out
                    </button>
                </div>
            </section>
        </main>
    );
}

export default ProfilePage;
