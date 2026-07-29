import HomePage from './components/HomePage';
import LoginPage from './components/LoginPage';
import MovieDetailPage from './components/MovieDetailPage';
import OnboardingPage from './components/OnboardingPage';
import ProfilePage from './components/ProfilePage';
import RegisterPage from './components/RegisterPage';
import { useAuth } from './features/auth/useAuth';
import { useAuthRouting } from './features/auth/useAuthRouting';
import { useLoginForm } from './features/auth/useLoginForm';
import { useNavigation } from './features/auth/useNavigation';
import { useRegisterForm } from './features/auth/useRegisterForm';
import { useMovieActions } from './features/interactions/useMovieActions';
import { useMovieDetail } from './features/movies/useMovieDetail';
import { useMovies } from './features/movies/useMovies';

function App() {
    const auth = useAuth();
    const { route, movieId, navigate, navigateToMovie } = useNavigation();
    const movies = useMovies();
    const movieDetail = useMovieDetail(
        route === 'movie-detail' ? movieId : null,
    );
    const loginForm = useLoginForm(auth.login);
    const registerForm = useRegisterForm(auth.register);
    const movieActions = useMovieActions(auth.userState, navigate);
    const authReady = auth.status !== 'idle' && auth.status !== 'loading';

    useAuthRouting(auth.userState, authReady, route, navigate);

    if (!authReady && route !== 'login' && route !== 'register') {
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
                onCreateAccount={() => navigate('register')}
            />
        );
    }

    if (route === 'register') {
        return (
            <RegisterPage
                email={registerForm.email}
                username={registerForm.username}
                password={registerForm.password}
                isSubmitting={auth.status === 'loading'}
                error={auth.error}
                onEmailChange={registerForm.setEmail}
                onUsernameChange={registerForm.setUsername}
                onPasswordChange={registerForm.setPassword}
                onSubmit={registerForm.submit}
                onSignIn={() => navigate('login')}
                onBrowseAsGuest={() => navigate('home')}
            />
        );
    }

    if (route === 'onboarding' && auth.user) {
        return (
            <OnboardingPage
                username={auth.user.username}
                isSubmitting={auth.status === 'loading'}
                error={auth.error}
                onComplete={auth.completeOnboarding}
                onLogout={auth.logout}
            />
        );
    }

    if (route === 'profile' && auth.user) {
        return (
            <ProfilePage
                user={auth.user}
                isSubmitting={auth.status === 'loading'}
                error={auth.error}
                onUpdate={auth.updateProfile}
                onBack={() => navigate('home')}
                onLogout={auth.logout}
            />
        );
    }

    if (route === 'movie-detail') {
        return (
            <MovieDetailPage
                movie={movieDetail.movie}
                isLoading={movieDetail.isLoading}
                error={movieDetail.error}
                userState={auth.userState}
                username={auth.user?.username || null}
                onBack={() => navigate('home')}
                onSignIn={() => navigate('login')}
                onProfile={() => navigate('profile')}
                onLogout={auth.logout}
                onWatch={movieActions.canWatchMovie}
                onWatchProgress={movieActions.recordWatchProgress}
                onRate={movieActions.rateMovie}
                onClearRating={movieActions.clearMovieRating}
                onReact={movieActions.reactToMovie}
                onShare={movieActions.shareMovie}
                interactionError={movieActions.error}
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
            onHome={() => navigate('home')}
            onSignIn={() => navigate('login')}
            onProfile={() => navigate('profile')}
            onLogout={auth.logout}
            onMovieClick={(selectedMovieId) => {
                movieActions.clickMovie(selectedMovieId);
                navigateToMovie(selectedMovieId);
            }}
            onWatch={movieActions.canWatchMovie}
            onRate={movieActions.rateMovie}
        />
    );
}

export default App;
