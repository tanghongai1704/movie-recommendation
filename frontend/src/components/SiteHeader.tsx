import type { AuthUserState } from '../features/auth/useAuth';

interface SiteHeaderProps {
    userState: AuthUserState;
    username: string | null;
    onHome: () => void;
    onSignIn: () => void;
    onProfile: () => void;
    onLogout: () => Promise<void>;
    primaryAction?: {
        label: string;
        onClick: () => void;
    };
}

function SiteHeader({
    userState,
    username,
    onHome,
    onSignIn,
    onProfile,
    onLogout,
    primaryAction,
}: SiteHeaderProps) {
    const isGuest = userState === 'guest';

    return (
        <header className="sticky top-0 z-30 border-b border-white/10 bg-[#05070b]/90 backdrop-blur">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
                <div className="flex min-w-0 items-center gap-6">
                    <button
                        type="button"
                        onClick={onHome}
                        className="truncate text-left text-xl font-black tracking-[0.25em] text-red-600 sm:text-2xl sm:tracking-[0.35em]"
                    >
                        STREAMVERSE
                    </button>
                    <nav
                        className="hidden items-center gap-4 text-sm font-medium text-zinc-300 md:flex"
                        aria-label="Primary navigation"
                    >
                        <button
                            type="button"
                            onClick={onHome}
                            className="transition hover:text-white"
                        >
                            Home
                        </button>
                        <a href="#" className="transition hover:text-white">
                            Series
                        </a>
                        <a href="#" className="transition hover:text-white">
                            Films
                        </a>
                        <a href="#" className="transition hover:text-white">
                            New &amp; Popular
                        </a>
                    </nav>
                </div>

                <div className="flex shrink-0 items-center gap-2 sm:gap-3">
                    {isGuest ? (
                        <button
                            type="button"
                            onClick={onSignIn}
                            className="rounded-full border border-white/15 px-3 py-2 text-sm font-medium text-zinc-200 transition hover:border-white/40 hover:bg-white/5 sm:px-4"
                        >
                            Sign In
                        </button>
                    ) : (
                        <>
                            <span className="hidden text-sm text-zinc-300 lg:inline">
                                Hi, {username}
                            </span>
                            <button
                                type="button"
                                onClick={onProfile}
                                className="rounded-full border border-white/15 px-3 py-2 text-sm font-medium text-zinc-200 transition hover:border-white/40 hover:bg-white/5 sm:px-4"
                            >
                                Profile
                            </button>
                            <button
                                type="button"
                                onClick={() => void onLogout()}
                                className="hidden rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:border-white/40 hover:bg-white/5 sm:inline-flex"
                            >
                                Sign Out
                            </button>
                        </>
                    )}
                    {primaryAction && (
                        <button
                            type="button"
                            onClick={primaryAction.onClick}
                            className="hidden rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500 xl:inline-flex"
                        >
                            {primaryAction.label}
                        </button>
                    )}
                </div>
            </div>
        </header>
    );
}

export default SiteHeader;
