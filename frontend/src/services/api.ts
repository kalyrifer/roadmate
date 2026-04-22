import axios, { AxiosError } from 'axios';
import type { 
  User, 
  UserProfile,
  Trip, 
  TripRequest, 
  Notification, 
  PaginatedResponse, 
  SearchParams, 
  Message, 
  ConversationListItem, 
  MessageListResponse, 
  ConversationListResponse,
  TripFormData,
  CreateRequestData,
  AuthResponse
} from '../types';

// Create axios instance
const axiosInstance = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
});

// Token management
const getToken = (): string | null => localStorage.getItem('token');
const setToken = (token: string | null) => {
  if (token) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
};
const clearToken = () => localStorage.removeItem('token');

// Request interceptor - add auth token
axiosInstance.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle 401 errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearToken();
    }
    return Promise.reject(error);
  }
);

// ================== Auth API ==================
export const authApi = {
  register: async (data: { email: string; password: string; name: string; phone: string }) => {
    const response = await axiosInstance.post<AuthResponse>('/auth/register', data);
    return response.data;
  },
  
  login: async (data: { email: string; password: string }) => {
    const response = await axiosInstance.post<AuthResponse>('/auth/login', data);
    if (response.data.access_token) {
      setToken(response.data.access_token);
    }
    return response.data;
  },
  
  logout: async () => {
    try {
      await axiosInstance.post('/auth/logout');
    } finally {
      clearToken();
    }
  },
  
  me: async () => {
    const response = await axiosInstance.get<User>('/auth/me');
    return response.data;
  },
};

// Helper to check if user is logged in
export const isLoggedIn = (): boolean => !!getToken();
export const getAccessToken = getToken;
export const setAccessToken = setToken;

// ================== Trips API ==================
export const tripsApi = {
  search: async (params: SearchParams) => {
    const response = await axiosInstance.get<PaginatedResponse<Trip>>('/trips', { params });
    return response.data;
  },
  
  getById: async (id: string) => {
    const response = await axiosInstance.get<Trip>(`/trips/${id}`);
    return response.data;
  },
  
  create: async (data: TripFormData) => {
    const response = await axiosInstance.post<Trip>('/trips', data);
    return response.data;
  },
  
  update: async (id: string, data: Partial<TripFormData>) => {
    const response = await axiosInstance.put<Trip>(`/trips/${id}`, data);
    return response.data;
  },
  
  delete: async (id: string) => {
    await axiosInstance.delete(`/trips/${id}`);
  },
  
  getMyTrips: async (role?: string) => {
    const response = await axiosInstance.get<PaginatedResponse<Trip>>('/trips/my', { 
      params: { role } 
    });
    return response.data;
  },
  
  createRequest: async (tripId: string, data: CreateRequestData) => {
    // Backend ожидает JSON body: { seats_requested, message }
    // Backend возвращает обёртку: { data: TripRequest, message: string }
    const response = await axiosInstance.post<{ data: TripRequest }>(
      `/trips/${tripId}/requests`,
      data
    );
    return response.data.data;
  },
  
  getTripRequests: async (tripId: string) => {
    const response = await axiosInstance.get<PaginatedResponse<TripRequest>>(`/trips/${tripId}/requests`);
    return response.data;
  },
};

// ================== Requests API ==================
export const requestsApi = {
  getMy: async (status?: string) => {
    const response = await axiosInstance.get<PaginatedResponse<TripRequest>>('/requests/my', { 
      params: { status } 
    });
    return response.data;
  },
  
  updateStatus: async (requestId: string, status: 'confirmed' | 'rejected') => {
    const response = await axiosInstance.put<TripRequest>(`/requests/${requestId}`, { status });
    return response.data;
  },
};

// ================== Users API ==================
export const usersApi = {
  // Получить профиль текущего пользователя
  getMyProfile: async () => {
    const response = await axiosInstance.get<UserProfile>('/users/me');
    return response.data;
  },
  
  // Обновить профиль текущего пользователя
  updateMyProfile: async (data: { name?: string; phone?: string; bio?: string; language?: string }) => {
    const formData = new FormData();
    if (data.name !== undefined) formData.append('name', data.name);
    if (data.phone !== undefined) formData.append('phone', data.phone);
    if (data.bio !== undefined) formData.append('bio', data.bio);
    if (data.language !== undefined) formData.append('language', data.language);
    
    const response = await axiosInstance.put<UserProfile>('/users/me', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  // Получить профиль пользователя по ID
  getById: async (id: string) => {
    const response = await axiosInstance.get<UserProfile>(`/users/public/${id}`);
    return response.data;
  },
  
  // Обновить профиль пользователя (для админов)
  update: async (id: string, data: { name?: string; phone?: string; bio?: string }) => {
    const response = await axiosInstance.put<UserProfile>(`/users/${id}`, data);
    return response.data;
  },
  
  getTrips: async (id: string, role?: string) => {
    const response = await axiosInstance.get<PaginatedResponse<Trip>>(`/users/${id}/trips`, { 
      params: { role } 
    });
    return response.data;
  },
};

// ================== Notifications API ==================
export const notificationsApi = {
  getAll: async (isRead?: boolean) => {
    const response = await axiosInstance.get<PaginatedResponse<Notification>>('/notifications', { 
      params: { is_read: isRead } 
    });
    return response.data;
  },
  
  markAsRead: async (id: string) => {
    const response = await axiosInstance.put<Notification>(`/notifications/${id}/read`);
    return response.data;
  },
  
  markAllAsRead: async () => {
    await axiosInstance.put('/notifications/read-all');
  },
};

// ================== Chat API ==================
export const chatApi = {
  getConversations: async () => {
    const response = await axiosInstance.get<ConversationListResponse>('/chat/conversations');
    return response.data;
  },
  
  getOrCreateConversation: async (tripId: string, passengerId: string) => {
    const response = await axiosInstance.post<ConversationListItem>('/chat/conversations', {
      trip_id: tripId,
      passenger_id: passengerId,
    });
    return response.data;
  },
  
  getMessages: async (conversationId: string, skip?: number, limit?: number) => {
    const response = await axiosInstance.get<MessageListResponse>(
      `/chat/conversations/${conversationId}/messages`,
      { params: { skip, limit } }
    );
    return response.data;
  },
  
  sendMessage: async (conversationId: string, content: string) => {
    const response = await axiosInstance.post<Message>(
      `/chat/conversations/${conversationId}/messages`,
      { conversation_id: conversationId, content }
    );
    return response.data;
  },
};

// ================== Reviews API ==================
export const reviewsApi = {
  getForUser: async (userId: string, page: number = 1, pageSize: number = 20) => {
    const response = await axiosInstance.get<PaginatedResponse<any>>(`/reviews/user/${userId}`, {
      params: { status_filter: 'published', page, page_size: pageSize },
    });
    return response.data;
  },
  
  getTripReviews: async (tripId: string, page: number = 1, pageSize: number = 20) => {
    const response = await axiosInstance.get<PaginatedResponse<any>>(`/reviews/trip/${tripId}`, {
      params: { status_filter: 'published', page, page_size: pageSize },
    });
    return response.data;
  },
  
  create: async (data: { trip_id: string; target_id: string; rating: number; text?: string }) => {
    const response = await axiosInstance.post<any>('/reviews', data);
    return response.data;
  },
  
  checkCanReview: async (tripId: string): Promise<{ can_review: boolean; reason: string }> => {
    const response = await axiosInstance.get<{ can_review: boolean; reason: string }>(
      `/reviews/me/trip/${tripId}/can-review`
    );
    return response.data;
  },
  
  updateStatus: async (reviewId: string, status: string) => {
    const response = await axiosInstance.put<any>(`/reviews/${reviewId}`, { status });
    return response.data;
  },
  
  delete: async (reviewId: string) => {
    await axiosInstance.delete(`/reviews/${reviewId}`);
  },
};

// Export default API object
export const api = {
  auth: authApi,
  trips: tripsApi,
  requests: requestsApi,
  users: usersApi,
  notifications: notificationsApi,
  chat: chatApi,
  reviews: reviewsApi,
};

export default api;
