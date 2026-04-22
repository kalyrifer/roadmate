import { api } from './client';

export type ReviewStatus = 'pending' | 'published' | 'rejected';

export interface Review {
  id: string;
  trip_id: string;
  author_id: string;
  target_id: string;
  rating: number;
  text?: string;
  status: ReviewStatus;
  created_at: string;
  updated_at: string;
}

export interface ReviewCreate {
  trip_id: string;
  target_id: string;
  rating: number;
  text?: string;
}

export interface ReviewListResponse {
  items: Review[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const reviewsApi = {
  create: async (data: ReviewCreate): Promise<Review> => {
    const response = await api.post<Review>('/reviews', data);
    return response.data;
  },

  getUserReviews: async (
    userId: string,
    params?: {
      status_filter?: ReviewStatus;
      page?: number;
      page_size?: number;
    }
  ): Promise<ReviewListResponse> => {
    const response = await api.get<ReviewListResponse>(`/reviews/user/${userId}`, {
      params,
    });
    return response.data;
  },

  getTripReviews: async (
    tripId: string,
    params?: {
      status_filter?: ReviewStatus;
      page?: number;
      page_size?: number;
    }
  ): Promise<ReviewListResponse> => {
    const response = await api.get<ReviewListResponse>(`/reviews/trip/${tripId}`, {
      params,
    });
    return response.data;
  },

  updateStatus: async (
    reviewId: string,
    status: ReviewStatus
  ): Promise<Review> => {
    const response = await api.put<Review>(`/reviews/${reviewId}`, { status });
    return response.data;
  },

  delete: async (reviewId: string): Promise<void> => {
    await api.delete(`/reviews/${reviewId}`);
  },

  checkCanReview: async (tripId: string): Promise<{
    can_review: boolean;
    reason: string;
  }> => {
    const response = await api.get<{
      can_review: boolean;
      reason: string;
    }>(`/reviews/me/trip/${tripId}/can-review`);
    return response.data;
  },

  getForUser: async (
    userId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ReviewListResponse> => {
    const response = await api.get<ReviewListResponse>(`/reviews/user/${userId}`, {
      params: { status_filter: 'published', page, page_size: pageSize },
    });
    return response.data;
  },
};

export default reviewsApi;