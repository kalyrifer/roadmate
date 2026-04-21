import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Input } from '../components/ui';
import { chatApi } from '../services/api/chat';
import { useAuthStore } from '../stores/auth';
import styles from './ChatPage.module.css';

export default function ChatPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const userId = useAuthStore((state) => state.user?.id);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messageText, setMessageText] = useState('');

  const {
    data: conversation,
    isLoading: convLoading,
  } = useQuery({
    queryKey: ['conversation', id],
    queryFn: () => chatApi.getConversation(id!),
    enabled: !!id,
  });

  const {
    data: messagesData,
    isLoading: msgsLoading,
  } = useQuery({
    queryKey: ['messages', id],
    queryFn: () => chatApi.getMessages(id!, 1, 100),
    enabled: !!id,
  });

  const sendMutation = useMutation({
    mutationFn: (content: string) => chatApi.sendMessage(id!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', id] });
      queryClient.invalidateQueries({ queryKey: ['conversation', id] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setMessageText('');
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesData?.items]);

  const handleSend = () => {
    if (!messageText.trim()) return;
    sendMutation.mutate(messageText.trim());
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (convLoading || msgsLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.loading}>Loading...</div>
        </div>
      </div>
    );
  }

  const otherParticipant = conversation?.participants?.find((p) => p.user_id !== userId);
  
  const otherName = otherParticipant?.user?.first_name && otherParticipant?.user?.last_name
    ? `${otherParticipant.user.first_name} ${otherParticipant.user.last_name}`
    : null;
  
  const tripName = conversation?.trip?.from_city && conversation?.trip?.to_city
    ? `${conversation.trip.from_city} → ${conversation.trip.to_city}`
    : null;
  
  const displayName = otherName || tripName || 'Chat';

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.avatar}>
            {otherParticipant?.user?.avatar_url ? (
              <img 
                src={otherParticipant.user.avatar_url} 
                alt={displayName}
              />
            ) : (
              <div className={styles.avatarPlaceholder}>
                {(displayName || 'C').charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          <div className={styles.headerInfo}>
            <div className={styles.headerName}>{displayName}</div>
            {conversation?.trip && (
              <div className={styles.headerTrip}>
                {conversation.trip.from_city} → {conversation.trip.to_city}
                {conversation.trip.departure_date && (
                  <span className={styles.headerDate}>
                    {new Date(conversation.trip.departure_date).toLocaleDateString('ru-RU', {
                      day: 'numeric',
                      month: 'short',
                    })}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className={styles.messages}>
        {messagesData?.items?.map((msg) => {
          const isOwn = msg.sender_id === userId;
          return (
            <div 
              key={msg.id} 
              className={`${styles.message} ${isOwn ? styles.own : styles.other}`}
            >
              <div className={styles.messageContent}>
                {msg.content}
              </div>
              <div className={styles.messageTime}>
                {formatTime(msg.created_at)}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        <textarea
          className={styles.input}
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={t('chat.sendMessage')}
          rows={1}
        />
        <Button 
          onClick={handleSend}
          disabled={!messageText.trim() || sendMutation.isPending}
        >
          {sendMutation.isPending ? '...' : t('chat.send')}
        </Button>
      </div>
    </div>
  );
}