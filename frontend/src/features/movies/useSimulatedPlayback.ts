import { useCallback, useEffect, useState } from 'react';

export function useSimulatedPlayback(
    runtimeMinutes: number | null,
    onPlayAttempt: () => boolean,
    onWatchMilestone: (progress: number) => void,
    resetKey: string | null,
) {
    const durationSeconds = Math.max(0, Math.round((runtimeMinutes || 0) * 60));
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [hasRecordedWatch, setHasRecordedWatch] = useState(false);

    useEffect(() => {
        setElapsedSeconds(0);
        setIsPlaying(false);
        setHasRecordedWatch(false);
    }, [durationSeconds, resetKey]);

    useEffect(() => {
        if (!isPlaying || durationSeconds === 0) {
            return;
        }

        const timer = window.setInterval(() => {
            setElapsedSeconds((current) =>
                Math.min(current + 1, durationSeconds),
            );
        }, 1000);

        return () => window.clearInterval(timer);
    }, [durationSeconds, isPlaying]);

    useEffect(() => {
        if (isPlaying && elapsedSeconds >= durationSeconds) {
            setIsPlaying(false);
        }
    }, [durationSeconds, elapsedSeconds, isPlaying]);

    useEffect(() => {
        if (
            isPlaying
            && !hasRecordedWatch
            && durationSeconds > 0
            && elapsedSeconds / durationSeconds >= 0.6
        ) {
            setHasRecordedWatch(true);
            onWatchMilestone(0.6);
        }
    }, [
        durationSeconds,
        elapsedSeconds,
        hasRecordedWatch,
        isPlaying,
        onWatchMilestone,
    ]);

    const togglePlayback = useCallback((): void => {
        if (isPlaying) {
            setIsPlaying(false);
            return;
        }
        if (durationSeconds === 0 || !onPlayAttempt()) {
            return;
        }
        if (elapsedSeconds >= durationSeconds) {
            setElapsedSeconds(0);
        }
        setIsPlaying(true);
    }, [durationSeconds, elapsedSeconds, isPlaying, onPlayAttempt]);

    const seek = useCallback(
        (seconds: number): void => {
            const nextElapsed = Math.min(
                Math.max(0, seconds),
                durationSeconds,
            );
            setElapsedSeconds(nextElapsed);
            if (nextElapsed >= durationSeconds) {
                setIsPlaying(false);
            }
        },
        [durationSeconds],
    );

    return {
        durationSeconds,
        elapsedSeconds,
        isPlaying,
        progress:
            durationSeconds > 0 ? (elapsedSeconds / durationSeconds) * 100 : 0,
        togglePlayback,
        seek,
    };
}
