import { useState, type FormEvent } from 'react';
import type { LoginRequest, UserProfile } from '../../types/api';

type Login = (credentials: LoginRequest) => Promise<UserProfile | null>;

export function useLoginForm(login: Login) {
    const [username, setUsername] = useState('demo');
    const [password, setPassword] = useState('password123');

    const submit = (event: FormEvent<HTMLFormElement>): void => {
        event.preventDefault();
        void login({ username, password });
    };

    return {
        username,
        password,
        setUsername,
        setPassword,
        submit,
    };
}
