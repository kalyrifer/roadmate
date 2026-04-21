import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Skeleton } from '../components/ui';
import { chatApi } from '../services/api/chat';
import { useAuthStore } from '../stores/auth';
import styles from './ChatListPage.module.css';

interface ConversationWithOther {
  id: string;
  trip_id: string;
  last_message_at?: string;
  last_message?: {
    id: string;
    content: string;
    created_at: string;
    sender_id: string;
  };
  trip?: {
    id: string;
    from_city: string;
    to_city: string;
    departure_date?: string;
    departure_time_start?: string;
  };
  participants?: Array<{
    user_id: string;
    user?: {
      id: string;
      first_name: string;
      last_name: string;
      avatar_url?: string;
    };
  }>;
  otherUser: {
    id: string;
    name: string;
    avatar_url?: string;
  };
}

export default function ChatListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const userId = useAuthStore((state) => state.user?.id);

  const {
    data: conversationsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => chatApi.getConversations(1, 50),
  });

  const conversations = useMemo<ConversationWithOther[]>(() => {
    if (!conversationsData?.items || !userId) return [];
    
    return conversationsData.items.map((conv) => {
      const otherParticipant = conv.participants?.find((p) => p.user_id !== userId);
      const otherUser = otherParticipant?.user;
      
      // First try trip name if available
      const tripName = conv.trip?.from_city && conv.trip?.to_city
        ? `${conv.trip.from_city} → ${conv.trip.to_city}`
        : null;
      
      // Then try other participant's name
      const otherName = otherUser?.first_name && otherUser?.last_name
        ? `${otherUser.first_name} ${otherUser.last_name}`
        : null;

      return {
        ...conv,
        otherUser: {
          id: (otherUser?.id || otherParticipant?.user_id) || '',
          name: otherName || tripName || 'Unknown',
          avatar_url: otherUser?.avatar_url,
        },
      };
    });
  }, [conversationsData, userId]);

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return t('chat.yesterday');
    } else if (days < 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    }
    return date.toLocaleDateString([], { day: 'numeric', month: 'short' });
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>{t('chat.title')}</h1>
        </div>
        <div className={styles.list}>
          {[1, 2, 3].map((i) => (
            <Card key={i} className={styles.card}>
              <div className={styles.avatar}>
                <Skeleton variant="circular" width={48} height={48} />
              </div>
              <div className={styles.content}>
                <Skeleton variant="text" width="60%" height={20} />
                <Skeleton variant="text" width="80%" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <Card className={styles.card}>
          <div className={styles.error}>{t('errors.serverError')}</div>
        </Card>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>{t('chat.title')}</h1>
      </div>

      {conversations.length === 0 && (
        <div className={styles.emptyState}>{t('chat.empty')}</div>
      )}

      {conversations.length > 0 && (
        <div className={styles.list}>
          {conversations.map((conv) => (
            <Card 
              key={conv.id} 
              className={styles.card}
              onClick={() => navigate(`/chat/${conv.id}`)}
            >
              <div className={styles.avatar}>
                {conv.otherUser.avatar_url ? (
                  <img 
                    src={conv.otherUser.avatar_url} 
                    alt={conv.otherUser.name}
                    className={styles.avatarImg}
                  />
                ) : (
                  <div className={styles.avatarPlaceholder}>
                    {conv.otherUser.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              
              <div className={styles.content}>
                <div className={styles.topRow}>
                  <span className={styles.name}>{conv.otherUser.name}</span>
                  <span className={styles.time}>
                    {formatTime(conv.last_message?.created_at || conv.last_message_at)}
                  </span>
                </div>
                
                <div className={styles.trip}>
                  {conv.trip?.from_city} → {conv.trip?.to_city}
                  {conv.trip?.departure_date && (
                    <span className={styles.date}>
                      {new Date(conv.trip.departure_date).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'short',
                      })}
                    </span>
                  )}
                </div>
                
                <div className={styles.lastMessage}>
                  {conv.last_message?.content || t('chat.noMessages')}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}