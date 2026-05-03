import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, Skeleton } from '../components/ui';
import { chatApi, Conversation, ConversationParticipantUser } from '../services/api/chat';
import { useAuthStore } from '../stores/auth';
import styles from './ChatListPage.module.css';

interface PreparedConversation extends Conversation {
  routeTitle: string;
  participantNames: string[];
  otherParticipants: ConversationParticipantUser[];
  unread: boolean;
  searchHaystack: string;
}

function getInitials(...parts: (string | undefined)[]): string {
  return parts
    .filter(Boolean)
    .map((p) => (p ?? '').trim().charAt(0).toUpperCase())
    .join('')
    .slice(0, 2);
}

function getFullName(user?: ConversationParticipantUser): string {
  if (!user) return '';
  return `${user.first_name || ''} ${user.last_name || ''}`.trim();
}

function formatRouteDate(dateStr?: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
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

export default function ChatListPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const userId = useAuthStore((state) => state.user?.id);
  const [searchTerm, setSearchTerm] = useState('');

  const {
    data: conversationsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => chatApi.getConversations(1, 50),
  });

  const conversations = useMemo<PreparedConversation[]>(() => {
    if (!conversationsData?.items || !userId) return [];

    return conversationsData.items.map((conv) => {
      const participants = conv.participants || [];
      const otherParticipants = participants
        .filter((p) => p.user_id !== userId)
        .map((p) => p.user)
        .filter((u): u is ConversationParticipantUser => Boolean(u));

      const participantNames = otherParticipants
        .map((u) => getFullName(u))
        .filter(Boolean);

      const routeTitle =
        conv.trip?.from_city && conv.trip?.to_city
          ? `${conv.trip.from_city} → ${conv.trip.to_city}`
          : t('chat.title');

      const me = participants.find((p) => p.user_id === userId);
      const unread = !!(
        conv.last_message &&
        conv.last_message.sender_id !== userId &&
        me?.last_read_message_id !== conv.last_message.id
      );

      const searchHaystack = [routeTitle, ...participantNames, conv.last_message?.content || '']
        .join(' ')
        .toLowerCase();

      return {
        ...conv,
        routeTitle,
        participantNames,
        otherParticipants,
        unread,
        searchHaystack,
      };
    });
  }, [conversationsData, userId, t]);

  const filteredConversations = useMemo(() => {
    if (!searchTerm.trim()) return conversations;
    const term = searchTerm.toLowerCase();
    return conversations.filter((c) => c.searchHaystack.includes(term));
  }, [conversations, searchTerm]);

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

  return (
    <div className={styles.container}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>{t('chat.title')}</h1>
        <p className={styles.pageSubtitle}>{t('chat.subtitle')}</p>
      </div>

      <div className={styles.searchWrap}>
        <span className={styles.searchIcon} aria-hidden>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={t('chat.searchPlaceholder')}
          className={styles.searchInput}
        />
      </div>

      {isLoading && (
        <div className={styles.list}>
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className={styles.card}>
              <Skeleton variant="circular" width={48} height={48} />
              <div className={styles.cardContent}>
                <Skeleton variant="text" width="55%" height={18} />
                <Skeleton variant="text" width="80%" height={14} />
              </div>
              <Skeleton variant="text" width={40} height={14} />
            </Card>
          ))}
        </div>
      )}

      {!isLoading && error && (
        <Card className={styles.errorCard}>{t('errors.serverError')}</Card>
      )}

      {!isLoading && !error && conversations.length === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon} aria-hidden>
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <p className={styles.emptyTitle}>{t('chat.empty')}</p>
          <p className={styles.emptyHint}>{t('chat.emptyHint')}</p>
        </div>
      )}

      {!isLoading && !error && conversations.length > 0 && filteredConversations.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>{t('chat.noSearchResults')}</p>
        </div>
      )}

      {!isLoading && filteredConversations.length > 0 && (
        <div className={styles.list}>
          {filteredConversations.map((conv) => {
            const tripDate = formatRouteDate(conv.trip?.departure_date);
            const lastMessageTime = formatTime(conv.last_message?.created_at || conv.last_message_at);
            const lastMessageText = conv.last_message?.content || t('chat.noMessages');
            const isOwnLast = conv.last_message && conv.last_message.sender_id === userId;
            const lastSenderUser =
              conv.last_message && !isOwnLast
                ? conv.participants?.find((p) => p.user_id === conv.last_message?.sender_id)?.user
                : undefined;
            const lastSenderLabel = isOwnLast
              ? `${t('chat.you')}: `
              : lastSenderUser
                ? `${getFullName(lastSenderUser).split(' ')[0]}: `
                : '';

            const totalParticipants = conv.participants?.length ?? 0;

            return (
              <Card
                key={conv.id}
                className={`${styles.card} ${conv.unread ? styles.cardUnread : ''}`}
                onClick={() => navigate(`/chat/${conv.id}`)}
              >
                <div className={styles.avatarStack} aria-hidden>
                  {conv.otherParticipants.slice(0, 2).map((u, idx) => (
                    <div
                      key={u.id}
                      className={`${styles.avatar} ${idx === 1 ? styles.avatarSecondary : ''}`}
                    >
                      {u.avatar_url ? (
                        <img src={u.avatar_url} alt="" />
                      ) : (
                        <span className={styles.avatarInitials}>{getInitials(u.first_name, u.last_name)}</span>
                      )}
                    </div>
                  ))}
                  {conv.otherParticipants.length === 0 && (
                    <div className={styles.avatar}>
                      <span className={styles.avatarInitials}>
                        {getInitials(conv.trip?.from_city, conv.trip?.to_city)}
                      </span>
                    </div>
                  )}
                </div>

                <div className={styles.cardContent}>
                  <div className={styles.cardTopRow}>
                    <span className={styles.routeTitle}>{conv.routeTitle}</span>
                    {lastMessageTime && (
                      <span className={`${styles.time} ${conv.unread ? styles.timeUnread : ''}`}>
                        {lastMessageTime}
                      </span>
                    )}
                  </div>
                  <div className={styles.metaRow}>
                    {tripDate && <span className={styles.metaPill}>{tripDate}</span>}
                    <span className={styles.metaSeparator}>·</span>
                    <span className={styles.metaText}>
                      {totalParticipants} {pluralizeParticipants(totalParticipants, i18n.language)}
                    </span>
                  </div>
                  <div className={`${styles.lastMessage} ${conv.unread ? styles.lastMessageUnread : ''}`}>
                    <span className={styles.lastSender}>{lastSenderLabel}</span>
                    {lastMessageText}
                  </div>
                </div>

                {conv.unread && <span className={styles.unreadDot} aria-label={t('chat.unread')} />}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
