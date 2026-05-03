import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  chatApi,
  ConversationParticipant,
  ConversationParticipantUser,
  Message,
} from '../services/api/chat';
import { useAuthStore } from '../stores/auth';
import styles from './ChatPage.module.css';

function getFullName(user?: ConversationParticipantUser): string {
  if (!user) return '';
  return `${user.first_name || ''} ${user.last_name || ''}`.trim();
}

function getInitials(user?: ConversationParticipantUser): string {
  if (!user) return '?';
  const a = (user.first_name || '').trim().charAt(0).toUpperCase();
  const b = (user.last_name || '').trim().charAt(0).toUpperCase();
  return (a + b).slice(0, 2) || '?';
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function formatDateSeparator(date: Date, t: (k: string) => string): string {
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (isSameDay(date, today)) return t('chat.today');
  if (isSameDay(date, yesterday)) return t('chat.yesterday');
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function pluralizeParticipants(count: number, lang: string): string {
  if (lang.startsWith('ru')) {
    const mod10 = count % 10;
    const mod100 = count % 100;
    if (mod10 === 1 && mod100 !== 11) return 'участник';
    if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return 'участника';
    return 'участников';
  }
  return count === 1 ? 'participant' : 'participants';
}

interface MessageGroup {
  type: 'date';
  key: string;
  date: Date;
}
interface MessageItem {
  type: 'msg';
  key: string;
  message: Message;
  showSenderHeader: boolean;
  showTail: boolean;
}
type FlatItem = MessageGroup | MessageItem;

export default function ChatPage() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const userId = useAuthStore((state) => state.user?.id);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [messageText, setMessageText] = useState('');

  const { data: conversation, isLoading: convLoading } = useQuery({
    queryKey: ['conversation', id],
    queryFn: () => chatApi.getConversation(id!),
    enabled: !!id,
  });

  const { data: messagesData, isLoading: msgsLoading } = useQuery({
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
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    },
  });

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesData?.items]);

  // Auto-grow textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [messageText]);

  const handleSend = () => {
    if (!messageText.trim() || sendMutation.isPending) return;
    sendMutation.mutate(messageText.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const participants = conversation?.participants || [];
  const otherParticipants: ConversationParticipantUser[] = participants
    .filter((p: ConversationParticipant) => p.user_id !== userId)
    .map((p) => p.user)
    .filter((u): u is ConversationParticipantUser => Boolean(u));

  const senderById = useMemo(() => {
    const map: Record<string, ConversationParticipantUser> = {};
    participants.forEach((p) => {
      if (p.user) map[p.user_id] = p.user;
    });
    return map;
  }, [participants]);

  const flatItems = useMemo<FlatItem[]>(() => {
    const items = messagesData?.items || [];
    const out: FlatItem[] = [];
    let prevDate: Date | null = null;
    let prevSenderId: string | null = null;
    let prevTime = 0;

    items.forEach((msg, idx) => {
      const date = new Date(msg.created_at);

      if (!prevDate || !isSameDay(prevDate, date)) {
        out.push({ type: 'date', key: `d-${msg.id}`, date });
        prevSenderId = null;
      }

      const next = items[idx + 1];
      const nextDate = next ? new Date(next.created_at) : null;
      const sameSenderAsPrev =
        prevSenderId === msg.sender_id && date.getTime() - prevTime < 5 * 60 * 1000;
      const sameSenderAsNext =
        next && next.sender_id === msg.sender_id && nextDate && isSameDay(date, nextDate);

      out.push({
        type: 'msg',
        key: msg.id,
        message: msg,
        showSenderHeader: !sameSenderAsPrev,
        showTail: !sameSenderAsNext,
      });

      prevDate = date;
      prevSenderId = msg.sender_id;
      prevTime = date.getTime();
    });

    return out;
  }, [messagesData?.items]);

  const tripRoute =
    conversation?.trip?.from_city && conversation?.trip?.to_city
      ? `${conversation.trip.from_city} → ${conversation.trip.to_city}`
      : t('chat.title');

  const tripDate = conversation?.trip?.departure_date
    ? new Date(conversation.trip.departure_date).toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
      })
    : '';

  const tripTime = conversation?.trip?.departure_time_start || '';

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <button
          type="button"
          className={styles.backButton}
          onClick={() => navigate('/chat')}
          aria-label={t('common.back')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
        </button>

        <div className={styles.headerInfo}>
          <div className={styles.headerTitle}>{tripRoute}</div>
          <div className={styles.headerSubtitle}>
            {participants.length} {pluralizeParticipants(participants.length, i18n.language)}
            {tripDate && (
              <>
                <span className={styles.dot}>·</span>
                <span>{tripDate}{tripTime ? `, ${tripTime}` : ''}</span>
              </>
            )}
          </div>
        </div>

        {conversation?.trip?.id && (
          <button
            type="button"
            className={styles.tripButton}
            onClick={() => navigate(`/trips/${conversation.trip!.id}`)}
            aria-label={t('chat.viewTrip')}
          >
            {t('chat.viewTrip')}
          </button>
        )}
      </header>

      {otherParticipants.length > 0 && (
        <div className={styles.participantsBar} aria-label={pluralizeParticipants(otherParticipants.length, i18n.language)}>
          {otherParticipants.map((u) => (
            <div key={u.id} className={styles.participantChip} title={getFullName(u)}>
              <div className={styles.participantAvatar}>
                {u.avatar_url ? <img src={u.avatar_url} alt="" /> : <span>{getInitials(u)}</span>}
              </div>
              <span className={styles.participantName}>{getFullName(u) || t('chat.participant')}</span>
            </div>
          ))}
        </div>
      )}

      <div className={styles.messagesWrap}>
        <div className={styles.messages} ref={messagesContainerRef}>
          {(convLoading || msgsLoading) && (
            <div className={styles.loadingState}>{t('common.loading')}</div>
          )}

          {!convLoading && !msgsLoading && flatItems.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon} aria-hidden>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <p className={styles.emptyTitle}>{t('chat.noMessages')}</p>
              <p className={styles.emptyHint}>{t('chat.firstMessageHint')}</p>
            </div>
          )}

          {flatItems.map((item) => {
            if (item.type === 'date') {
              return (
                <div key={item.key} className={styles.dateSeparator}>
                  <span>{formatDateSeparator(item.date, t)}</span>
                </div>
              );
            }
            const msg = item.message;
            const isOwn = msg.sender_id === userId;
            const sender = senderById[msg.sender_id];

            return (
              <div
                key={item.key}
                className={`${styles.messageRow} ${isOwn ? styles.messageRowOwn : styles.messageRowOther}`}
              >
                {!isOwn && (
                  <div className={styles.messageAvatarSlot}>
                    {item.showTail ? (
                      <div className={styles.messageAvatar} title={getFullName(sender)}>
                        {sender?.avatar_url ? (
                          <img src={sender.avatar_url} alt="" />
                        ) : (
                          <span>{getInitials(sender)}</span>
                        )}
                      </div>
                    ) : (
                      <div className={styles.messageAvatarSpacer} />
                    )}
                  </div>
                )}

                <div className={styles.messageBlock}>
                  {!isOwn && item.showSenderHeader && (
                    <div className={styles.messageSender}>
                      {getFullName(sender) || t('chat.participant')}
                    </div>
                  )}
                  <div
                    className={`${styles.bubble} ${
                      isOwn ? styles.bubbleOwn : styles.bubbleOther
                    } ${item.showTail ? styles.bubbleTail : ''}`}
                  >
                    <div className={styles.bubbleContent}>{msg.content}</div>
                    <div className={styles.bubbleTime}>{formatTime(msg.created_at)}</div>
                  </div>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className={styles.composer}>
        <textarea
          ref={textareaRef}
          className={styles.composerInput}
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.sendMessage')}
          rows={1}
          disabled={sendMutation.isPending}
        />
        <button
          type="button"
          className={styles.sendButton}
          onClick={handleSend}
          disabled={!messageText.trim() || sendMutation.isPending}
          aria-label={t('chat.send')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
