// Types for the RoadMate application

// ================== User Types ==================
export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  avatar_url?: string;
  rating?: number;
  created_at: string;
}

export interface ReviewAuthor {
  id: string;
  name: string;
  avatar_url?: string;
}

export interface Review {
  id: string;
  author_id: string;
  author?: ReviewAuthor | null;
  rating: number;
  text?: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  phone?: string;
  avatar_url?: string;
  bio?: string;
  rating_average: number;
  rating_count: number;
  trips_count: number;
  reviews: Review[];
  created_at: string;
}

export interface UserProfileUpdate {
  name?: string;
  phone?: string;
  bio?: string;
  language?: string;
  avatar?: File;
}

export interface Driver {
  id: string;
  name: string;
  avatar_url?: string;
  rating?: number;
  rating_average?: number;
  rating_count?: number;
  phone?: string;
}

// ================== Trip Types ==================
export type TripStatus = 'draft' | 'published' | 'active' | 'completed' | 'cancelled';

export interface Trip {
  id: string;
  driver_id: string;
  driver: Driver;
  from_city: string;
  from_address?: string;
  to_city: string;
  to_address?: string;
  departure_date: string;
  departure_time_start: string;
  departure_time_end?: string;
  is_time_range: boolean;
  arrival_time?: string;
  available_seats: number;
  total_seats: number;
  price_per_seat: number;
  description?: string;
  luggage_allowed: boolean;
  smoking_allowed: boolean;
  music_allowed: boolean;
  pets_allowed: boolean;
  car_model?: string;
  car_color?: string;
  car_license_plate?: string;
  status: TripStatus;
  created_at: string;
  updated_at?: string;
  passengers?: Passenger[];
}

export interface Passenger {
  id: string;
  name: string;
  seats_requested: number;
  avatar_url?: string;
  rating_average?: number;
}

export interface TripFormData {
  from_city: string;
  from_address?: string;
  to_city: string;
  to_address?: string;
  departure_date: string;
  departure_time_start: string;
  departure_time_end?: string;
  is_time_range?: boolean;
  arrival_time?: string;
  total_seats: number;
  price_per_seat: number;
  description?: string;
  luggage_allowed?: boolean;
  smoking_allowed?: boolean;
  music_allowed?: boolean;
  pets_allowed?: boolean;
  car_model?: string;
  car_color?: string;
  car_license_plate?: string;
}

// ================== Request Types ==================
export type RequestStatus = 'pending' | 'confirmed' | 'rejected' | 'cancelled';

export interface TripRequest {
  id: string;
  trip_id: string;
  passenger_id: string;
  passenger?: {
    id: string;
    first_name: string;
    last_name: string;
    avatar_url?: string;
    rating_average?: number;
    rating_count?: number;
  };
  seats_requested: number;
  message?: string;
  status: RequestStatus;
  created_at: string;
  updated_at?: string;
  confirmed_at?: string;
  rejected_at?: string;
  rejected_reason?: string;
  cancelled_at?: string;
  cancelled_by?: string;
  // Backend также может вернуть дополнительные поля для связи
  trip?: {
    id: string;
    from_city?: string;
    to_city?: string;
    departure_date?: string;
    departure_time_start?: string;
    available_seats?: number;
  };
}

export interface CreateRequestData {
  seats_requested: number;
  message?: string;
}

// ================== Notification Types ==================
export type NotificationType = 
  | 'request_received' 
  | 'request_confirmed' 
  | 'request_rejected' 
  | 'trip_cancelled';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  related_trip_id?: string;
  related_request_id?: string;
  created_at: string;
}

// ================== Pagination Types ==================
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SearchParams {
  from_city?: string;
  to_city?: string;
  date?: string;
  page?: number;
  page_size?: number;
}

// ================== Chat Types ==================
export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface ConversationListItem {
  id: string;
  trip_id: string;
  other_user_id: string;
  other_user_name: string;
  trip_from_city: string;
  trip_to_city: string;
  last_message?: string;
  last_message_time?: string;
  unread_count: number;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
}

export interface ConversationListResponse {
  items: ConversationListItem[];
  total: number;
}

// ================== Review Types ==================
export interface Review {
  id: string;
  trip_id: string;
  reviewer_id: string;
  reviewee_id: string;
  rating: number;
  comment?: string;
  created_at: string;
}

export interface CreateReviewData {
  trip_id: string;
  reviewee_id: string;
  rating: number;
  comment?: string;
}

// ================== API Response Types ==================
export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface ApiError {
  detail: string;
}
