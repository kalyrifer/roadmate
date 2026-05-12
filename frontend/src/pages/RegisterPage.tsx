import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { Button, Input, Card } from '../components/ui';
import { useAuthStore } from '../stores/auth';
import styles from './LoginPage.module.css';

interface RegisterForm {
  email: string;
  password: string;
  confirmPassword: string;
  name: string;
  phone?: string;
}

export default function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const registerUser = useAuthStore((state) => state.register);
  const [error, setError] = useState<string>('');
  
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>();
  const password = watch('password');

  const registerMutation = useMutation({
    mutationFn: (data: { email: string; password: string; name: string }) =>
      registerUser(data),
    onSuccess: () => {
      navigate('/');
    },
    onError: (err: unknown) => {
      let message: string | undefined;
      if (typeof err === 'string') {
        message = err;
      } else if (err instanceof Error && err.message) {
        message = err.message;
      }
      setError(message || t('errors.registerFailed'));
    },
  });

  const onSubmit = (data: RegisterForm) => {
    setError('');
    const { confirmPassword, ...registerData } = data;
    // Send data matching backend UserRegisterRequest schema
    const apiData = {
      email: registerData.email,
      password: registerData.password,
      name: registerData.name,
    };
    registerMutation.mutate(apiData);
  };

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <h1 className={styles.title}>{t('auth.register')}</h1>
        <p className={styles.subtitle}>{t('auth.registerSubtitle')}</p>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
          {error && <div className={styles.error}>{error}</div>}

          <Input
            label={t('auth.name')}
            type="text"
            placeholder={t('auth.namePlaceholder')}
            {...register('name', { required: t('errors.required') })}
            error={errors.name?.message}
          />

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
            label={t('auth.phone')}
            type="tel"
            placeholder={t('auth.phonePlaceholder')}
            {...register('phone')}
          />

          <Input
            label={t('auth.password')}
            type="password"
            placeholder={t('auth.passwordPlaceholder')}
            {...register('password', {
              required: t('errors.required'),
              minLength: {
                value: 8,
                message: t('errors.passwordMinLength'),
              },
              validate: (value) => {
                if (!/[A-Za-zА-Яа-яЁё]/.test(value) || !/\d/.test(value)) {
                  return t('errors.passwordWeakLettersDigits');
                }
                if (new Set(value).size === 1) {
                  return t('errors.passwordWeakRepeated');
                }
                const common = [
                  '12345678', '123456789', '1234567890',
                  'qwerty', 'qwerty123', 'qwertyuiop',
                  'password', 'password1', 'password123',
                  'passw0rd', '11111111', '00000000',
                  'abc12345', 'abcd1234', 'iloveyou',
                  'admin123', 'letmein', 'welcome1',
                  'qazwsx', 'qazwsx123', 'пароль123', 'йцукен123',
                ];
                if (common.includes(value.toLowerCase())) {
                  return t('errors.passwordWeakCommon');
                }
                return true;
              },
            })}
            error={errors.password?.message}
          />

          <Input
            label={t('auth.confirmPassword')}
            type="password"
            placeholder={t('auth.confirmPasswordPlaceholder')}
            {...register('confirmPassword', { 
              required: t('errors.required'),
              validate: (value) => 
                value === password || t('errors.passwordMismatch')
            })}
            error={errors.confirmPassword?.message}
          />

          <Button 
            type="submit" 
            variant="primary" 
            loading={registerMutation.isPending}
            className={styles.submitButton}
          >
            {t('auth.register')}
          </Button>
        </form>

        <p className={styles.footer}>
          {t('auth.hasAccount')}{' '}
          <Link to="/login" className={styles.link}>
            {t('auth.login')}
          </Link>
        </p>
      </Card>
    </div>
  );
}
