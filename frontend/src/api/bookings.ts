import apiClient from './axios';
import type { 
  Booking, 
  BookingCreate, 
  BookingBrief,
  BookingWithDetails
} from '../types';

export const bookingApi = {
  /**
   * Create a new booking (Guest)
   */
  createBooking: async (data: BookingCreate): Promise<Booking> => {
    const response = await apiClient.post('/api/v1/bookings/', data);
    return response.data;
  },

  /**
   * Get my bookings as a guest
   */
  getMyBookings: async (status?: string): Promise<BookingBrief[]> => {
    const response = await apiClient.get('/api/v1/bookings/my', {
      params: status ? { status } : {},
    });
    return response.data;
  },

  /**
   * Get bookings for my listings (Host only)
   */
  getHostBookings: async (status?: string): Promise<BookingBrief[]> => {
    const response = await apiClient.get('/api/v1/bookings/host', {
      params: status ? { status } : {},
    });
    return response.data;
  },

  /**
   * Get booking details by ID
   */
  getBookingById: async (id: number): Promise<BookingWithDetails> => {
    const response = await apiClient.get(`/api/v1/bookings/${id}`);
    return response.data;
  },

  /**
   * Confirm a booking (Host only)
   */
  confirmBooking: async (bookingId: number): Promise<Booking> => {
    const response = await apiClient.post(`/api/v1/bookings/${bookingId}/confirm`);
    return response.data;
  },

  /**
   * Reject a booking (Host only)
   */
  rejectBooking: async (bookingId: number, reason?: string): Promise<Booking> => {
    const response = await apiClient.post(`/api/v1/bookings/${bookingId}/reject`, {
      status: 'rejected',
      reason,
    });
    return response.data;
  },

  /**
   * Cancel a booking (Guest or Host)
   */
  cancelBooking: async (bookingId: number, reason?: string): Promise<Booking> => {
    const response = await apiClient.post(`/api/v1/bookings/${bookingId}/cancel`, {
      reason,
    });
    return response.data;
  },

  /**
   * Complete a booking (Host only, after checkout)
   */
  completeBooking: async (bookingId: number): Promise<Booking> => {
    const response = await apiClient.post(`/api/v1/bookings/${bookingId}/complete`);
    return response.data;
  },

  /**
   * Get available status transitions for a booking
   */
  getAvailableTransitions: async (bookingId: number): Promise<{
    booking_id: number;
    current_status: string;
    available_transitions: string[];
  }> => {
    const response = await apiClient.get(`/api/v1/bookings/${bookingId}/status-transitions`);
    return response.data;
  },
};
