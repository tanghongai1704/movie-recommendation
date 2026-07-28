import { useState, type FormEvent } from 'react';
import type { RegisterRequest, UserProfile } from '../../types/api';

type Register = (payload: RegisterRequest) => Promise<UserProfile | null>;

export function useRegisterForm(register: Register) {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const submit = (event: FormEvent<HTMLFormElement>): void => {
        event.preventDefault();
        void register({ email, username, password });
    };

    return {
        email,
        username,
        password,
        setEmail,
        setUsername,
        setPassword,
        submit,
    };
}
