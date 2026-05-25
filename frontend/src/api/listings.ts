import apiClient from './axios';
import type { 
  Listing, 
  ListingCreate, 
  ListingUpdate, 
  ListingSearchFilters,
  PaginatedResponse 
} from '../types';

export interface ImageUploadResponse {
  id: number;
  listing_id: number;
  image_url: string;
  is_primary: boolean;
  created_at: string;
}

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

  /**
   * Upload image for a listing
   */
  uploadImage: async (listingId: number, file: File): Promise<ImageUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(
      `/api/v1/listings/${listingId}/images/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Get images for a listing
   */
  getListingImages: async (listingId: number): Promise<ImageUploadResponse[]> => {
    const response = await apiClient.get(`/api/v1/listings/${listingId}/images`);
    return response.data;
  },

  /**
   * Delete an image
   */
  deleteImage: async (listingId: number, imageId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/listings/${listingId}/images/${imageId}`);
  },

  /**
   * Set primary image
   */
  setPrimaryImage: async (listingId: number, imageId: number): Promise<ImageUploadResponse> => {
    const response = await apiClient.put(`/api/v1/listings/${listingId}/images/${imageId}/primary`);
    return response.data;
  },

  /**
   * Toggle listing active status
   */
  toggleActive: async (listingId: number): Promise<Listing> => {
    const response = await apiClient.patch(`/api/v1/listings/${listingId}/toggle-active`);
    return response.data;
  },
};
