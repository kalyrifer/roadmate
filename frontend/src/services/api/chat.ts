import { api } from './client';
import { WS_URL } from '../../config';

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
  sender?: {
    id: string;
    first_name: string;
    last_name: string;
    avatar_url?: string;
  };
}

export interface TripInfo {
  id: string;
  from_city: string;
  to_city: string;
  departure_date?: string;
  departure_time_start?: string;
}

export interface Conversation {
  id: string;
  trip_id: string;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  participants: ConversationParticipant[];
  last_message?: Message;
  trip?: TripInfo;
}

export interface ConversationParticipantUser {
  id: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
}

export interface ConversationParticipant {
  id: string;
  conversation_id: string;
  user_id: string;
  is_muted: boolean;
  last_read_message_id?: string;
  joined_at: string;
  user?: ConversationParticipantUser;
}

export interface ConversationListResponse {
  items: Conversation[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SendMessageData {
  content: string;
}

class ChatService {
  private ws: WebSocket | null = null;
  private messageHandlers: ((message: Message) => void)[] = [];

  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${WS_URL}/chat?token=${token}`);

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data) as Message;
      this.messageHandlers.forEach((handler) => handler(message));
    };

    this.ws.onclose = () => {
      // Auto-reconnect logic could be added here
    };
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }

  sendWebSocketMessage(conversationId: string, content: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ conversation_id: conversationId, content }));
    }
  }

  onMessage(handler: (message: Message) => void): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
    };
  }

  // HTTP methods
  async getConversations(page = 1, limit = 20): Promise<ConversationListResponse> {
    const response = await api.get<ConversationListResponse>('/chat/conversations', {
      params: { page, page_size: limit },
    });
    return response.data;
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await api.get<Conversation>(`/chat/conversations/${conversationId}`);
    return response.data;
  }

  async getMessages(conversationId: string, page = 1, limit = 50): Promise<MessageListResponse> {
    const response = await api.get<MessageListResponse>(`/chat/conversations/${conversationId}/messages`, {
      params: { page, page_size: limit },
    });
    return response.data;
  }

  async createConversation(tripId: string, content: string): Promise<Conversation> {
    const response = await api.post<Conversation>('/chat/conversations/by-trip', {
      trip_id: tripId,
      content,
    });
    return response.data;
  }

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const response = await api.post<Message>(`/chat/conversations/${conversationId}/messages`, {
      content,
    });
    return response.data;
  }

  async markAsRead(conversationId: string, messageId: string): Promise<void> {
    await api.post(`/chat/conversations/${conversationId}/read`, {
      message_id: messageId,
    });
  }

  async getConversationsByTrip(tripId: string): Promise<ConversationListResponse> {
    const response = await api.get<ConversationListResponse>(`/chat/conversations/trip/${tripId}`);
    return response.data;
  }

  async createOrGetConversation(tripId: string, content: string): Promise<Conversation> {
    const response = await api.post<Conversation>('/chat/conversations/by-trip', {
      trip_id: tripId,
      content,
    });
    return response.data;
  }
}

export const chatApi = new ChatService();
export default chatApi;
