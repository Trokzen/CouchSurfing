import React, { useRef, useState } from 'react';
import { listingApi, type ImageUploadResponse } from '../api/listings';

interface ImageUploaderProps {
  listingId: number;
  onImagesChange?: () => void;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({ listingId, onImagesChange }) => {
  const [images, setImages] = useState<ImageUploadResponse[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load images on mount
  React.useEffect(() => {
    loadImages();
  }, [listingId]);

  const loadImages = async () => {
    try {
      const data = await listingApi.getListingImages(listingId);
      setImages(data);
    } catch (err) {
      console.error('Failed to load images:', err);
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
          setError(`File "${file.name}" is not an image`);
          continue;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          setError(`File "${file.name}" is too large (max 5MB)`);
          continue;
        }

        await listingApi.uploadImage(listingId, file);
      }
      
      await loadImages();
      onImagesChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload image');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (imageId: number) => {
    if (!confirm('Are you sure you want to delete this image?')) return;

    try {
      await listingApi.deleteImage(listingId, imageId);
      await loadImages();
      onImagesChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete image');
    }
  };

  const handleSetPrimary = async (imageId: number) => {
    try {
      await listingApi.setPrimaryImage(listingId, imageId);
      await loadImages();
      onImagesChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to set primary image');
    }
  };

  const primaryImage = images.find(img => img.is_primary);

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Listing Photos
        </label>
        <div className="flex items-center space-x-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            disabled={uploading}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100"
          />
          {uploading && (
            <span className="text-sm text-gray-500">Uploading...</span>
          )}
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </div>

      {images.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {images.map((image) => (
            <div key={image.id} className="relative group">
              <img
                src={image.image_url}
                alt="Listing"
                className={`w-full h-48 object-cover rounded-lg ${
                  image.is_primary ? 'ring-2 ring-blue-500' : ''
                }`}
              />
              {image.is_primary && (
                <span className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">
                  Primary
                </span>
              )}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all rounded-lg flex items-center justify-center space-x-2 opacity-0 group-hover:opacity-100">
                {!image.is_primary && (
                  <button
                    onClick={() => handleSetPrimary(image.id)}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                  >
                    Set Primary
                  </button>
                )}
                <button
                  onClick={() => handleDelete(image.id)}
                  className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {primaryImage && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Preview (Primary Image):</p>
          <img
            src={primaryImage.image_url}
            alt="Primary Preview"
            className="w-full h-64 object-cover rounded-lg"
          />
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
