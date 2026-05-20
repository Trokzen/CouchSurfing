import apiClient from './axios';
import type { 
  Listing, 
  ListingCreate, 
  ListingUpdate, 
  ListingSearchFilters,
  PaginatedResponse 
} from '../types';

export const listingApi = {
  /**
   * Create a new listing (Host only)
   */
  createListing: async (data: ListingCreate): Promise<Listing> => {
    const response = await apiClient.post('/api/v1/listings/', data);
    return response.data;
  },

  /**
   * Get listings by host ID
   */
  getHostListings: async (hostId: number, includeInactive = false): Promise<Listing[]> => {
    const response = await apiClient.get('/api/v1/listings/', {
      params: { host_id: hostId, include_inactive: includeInactive },
    });
    return response.data;
  },

  /**
   * Search listings with filters
   */
  searchListings: async (filters: ListingSearchFilters): Promise<PaginatedResponse<Listing>> => {
    const response = await apiClient.get('/api/v1/listings/search', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get listing by ID
   */
  getListingById: async (id: number): Promise<Listing> => {
    const response = await apiClient.get(`/api/v1/listings/${id}`);
    return response.data;
  },

  /**
   * Update listing (Owner or Moderator only)
   */
  updateListing: async (id: number, data: ListingUpdate): Promise<Listing> => {
    const response = await apiClient.put(`/api/v1/listings/${id}`, data);
    return response.data;
  },

  /**
   * Delete listing (Owner or Moderator only)
   */
  deleteListing: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/listings/${id}`);
  },

  /**
   * Check listing availability for dates
   */
  checkAvailability: async (listingId: number, startDate: string, endDate: string): Promise<{ listing_id: number; available: boolean }> => {
    const response = await apiClient.get(`/api/v1/listings/${listingId}/availability`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },
};
