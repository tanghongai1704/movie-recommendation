import HomePage from './components/HomePage';
import LoginPage from './components/LoginPage';
import OnboardingPage from './components/OnboardingPage';
import { useAuth } from './features/auth/useAuth';
import { useAuthRouting } from './features/auth/useAuthRouting';
import { useLoginForm } from './features/auth/useLoginForm';
import { useNavigation } from './features/auth/useNavigation';
import { useMovieActions } from './features/interactions/useMovieActions';
import { useMovies } from './features/movies/useMovies';

function App() {
    const auth = useAuth();
    const { route, navigate } = useNavigation();
    const movies = useMovies();
    const loginForm = useLoginForm(auth.login);
    const movieActions = useMovieActions(auth.userState, navigate);
    const authReady = auth.status !== 'idle' && auth.status !== 'loading';

    useAuthRouting(auth.userState, authReady, route, navigate);

    if (!authReady && route !== 'login') {
        return (
            <div className="grid min-h-screen place-items-center bg-[#05070b] text-zinc-300">
                Loading your experience…
            </div>
        );
    }

    if (route === 'login') {
        return (
            <LoginPage
                username={loginForm.username}
                password={loginForm.password}
                isSubmitting={auth.status === 'loading'}
                error={auth.error}
                onUsernameChange={loginForm.setUsername}
                onPasswordChange={loginForm.setPassword}
                onSubmit={loginForm.submit}
                onBrowseAsGuest={() => navigate('home')}
            />
        );
    }

    if (route === 'onboarding') {
        return (
            <OnboardingPage
                username={auth.user?.username || ''}
                onComplete={auth.completeOnboarding}
                onLogout={auth.logout}
            />
        );
    }

    return (
        <HomePage
            userState={auth.userState}
            username={auth.user?.username || null}
            movies={movies.movies}
            moviesLoading={movies.isLoading}
            moviesError={movies.error}
            interactionError={movieActions.error}
            onSignIn={() => navigate('login')}
            onLogout={auth.logout}
            onMovieClick={movieActions.clickMovie}
            onWatch={movieActions.watchMovie}
            onRate={movieActions.rateMovie}
        />
    );
}

export default App;
