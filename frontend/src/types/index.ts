export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  verification_status: VerificationStatus;
  created_at: string;
}

export type UserRole = 'guest' | 'host' | 'moderator';
export type VerificationStatus = 'unverified' | 'pending' | 'verified';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}

// ==================== Listing Types ====================

export interface Listing {
  id: number;
  host_id: number;
  title: string;
  description: string;
  city: string;
  address: string;
  capacity: number;
  amenities: string[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ListingBrief {
  id: number;
  title: string;
  city: string;
  capacity: number;
  is_active: boolean;
}

export interface ListingCreate {
  title: string;
  description: string;
  city: string;
  address: string;
  capacity: number;
  amenities?: string[];
  is_active?: boolean;
}

export interface ListingUpdate {
  title?: string;
  description?: string;
  city?: string;
  address?: string;
  capacity?: number;
  amenities?: string[];
  is_active?: boolean;
}

export interface ListingSearchFilters {
  city?: string;
  check_in?: string;
  check_out?: string;
  min_capacity?: number;
  page?: number;
  size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ==================== Booking Types ====================

export type BookingStatus = 'new' | 'pending' | 'confirmed' | 'rejected' | 'cancelled' | 'completed';

export interface Booking {
  id: number;
  guest_id: number;
  listing_id: number;
  start_date: string;
  end_date: string;
  status: BookingStatus;
  message?: string;
  created_at: string;
  updated_at: string;
}

export interface BookingWithDetails {
  id: number;
  guest_id: number;
  guest_name: string;
  listing_id: number;
  listing_title: string;
  listing_city: string;
  start_date: string;
  end_date: string;
  status: BookingStatus;
  message?: string;
  created_at: string;
  updated_at: string;
}

export interface BookingBrief {
  id: number;
  listing_id: number;
  listing_title: string;
  listing_city?: string;
  start_date: string;
  end_date: string;
  status: BookingStatus;
  message?: string;
}

export interface BookingCreate {
  listing_id: number;
  start_date: string;
  end_date: string;
  message?: string;
}

export interface BookingStatusChange {
  status: BookingStatus;
  reason?: string;
}

// ==================== Review Types ====================

export interface Review {
  id: number;
  booking_id: number;
  author_id: number;
  author_name: string;
  target_id: number;
  target_name: string;
  rating: number;
  comment: string;
  created_at: string;
}

export interface ReviewCreate {
  booking_id: number;
  target_id: number;
  rating: number;
  comment: string;
}

// ==================== Message Types ====================

export interface Message {
  id: number;
  sender_id: number;
  sender_name: string;
  receiver_id: number;
  receiver_name: string;
  booking_id?: number;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface MessageCreate {
  receiver_id: number;
  booking_id?: number;
  content: string;
}

export interface ConversationPreview {
  partner_id: number;
  partner_name: string;
  last_message: string;
  last_message_at: string;
  unread_count: number;
  partner_avatar?: string;
}
