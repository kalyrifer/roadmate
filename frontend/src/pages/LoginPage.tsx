import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Button, Input, Card } from '../components/ui';
import { useAuthStore } from '../stores/auth';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../services/api/auth';
import styles from './LoginPage.module.css';

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [error, setError] = useState<string>('');
  
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: LoginForm) => login(email, password),
    onSuccess: () => {
      navigate('/');
    },
    onError: (err: Error) => {
      if (err.message === 'AUTH_INVALID_CREDENTIALS') {
        setError(t('auth.invalidCredentials'));
      } else {
        setError(err.message || t('errors.loginFailed'));
      }
    },
  });

  const onSubmit = (data: LoginForm) => {
    setError('');
    loginMutation.mutate(data);
  };

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <h1 className={styles.title}>{t('auth.login')}</h1>
        <p className={styles.subtitle}>{t('auth.loginSubtitle')}</p>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          {error && <div className={styles.error}>{error}</div>}

          <Input
            label={t('auth.email')}
            type="email"
            placeholder={t('auth.emailPlaceholder')}
            {...register('email', { 
              required: t('errors.required'),
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: t('errors.invalidEmail')
              }
            })}
            error={errors.email?.message}
          />

          <Input
            label={t('auth.password')}
            type="password"
            placeholder={t('auth.passwordPlaceholder')}
            {...register('password', { 
              required: t('errors.required'),
              minLength: {
                value: 6,
                message: t('errors.passwordMinLength')
              }
            })}
            error={errors.password?.message}
          />

          <Button 
            type="submit" 
            variant="primary" 
            loading={loginMutation.isPending}
            className={styles.submitButton}
          >
            {t('auth.login')}
          </Button>
        </form>

        <p className={styles.footer}>
          {t('auth.noAccount')}{' '}
          <Link to="/register" className={styles.link}>
            {t('auth.register')}
          </Link>
        </p>
      </Card>
    </div>
  );
}
