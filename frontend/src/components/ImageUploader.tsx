import React, { useRef, useState } from 'react';
import { Button, Group, Stack, Text, Image, Badge, Box, Loader } from '@mantine/core';
import { IconUpload, IconTrash, IconStar, IconStarFilled } from '@tabler/icons-react';
import { listingApi, type ImageUploadResponse } from '../api/listings';
import { getImageUrl } from '../api/axios';

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
      await listingApi.deleteImage(imageId);
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
    <Stack gap="md">
      <Box>
        <Text fw={500} mb="sm">Listing Photos</Text>
        <Group gap="sm" align="flex-end">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            disabled={uploading}
            style={{ display: 'none' }}
            id={`file-input-${listingId}`}
          />
          <Button
            component="label"
            htmlFor={`file-input-${listingId}`}
            variant="outline"
            leftSection={<IconUpload size={18} />}
            disabled={uploading}
            loading={uploading}
          >
            {uploading ? 'Uploading...' : 'Select Images'}
          </Button>
          {uploading && <Loader size="sm" />}
        </Group>
        {error && (
          <Text c="red" size="sm" mt="xs">{error}</Text>
        )}
      </Box>

      {images.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: '16px'
        }}>
          {images.map((image) => (
            <Box
              key={image.id}
              style={{
                position: 'relative',
                borderRadius: '8px',
                overflow: 'hidden',
                border: image.is_primary ? '2px solid var(--mantine-color-blue-6)' : '1px solid var(--mantine-color-gray-3)',
              }}
            >
              <Image
                src={getImageUrl(image.image_url)}
                alt="Listing"
                height={150}
                fit="cover"
              />
              {image.is_primary && (
                <Badge
                  leftSection={<IconStarFilled size={12} />}
                  color="blue"
                  size="sm"
                  style={{
                    position: 'absolute',
                    top: '8px',
                    left: '8px',
                  }}
                >
                  Primary
                </Badge>
              )}
              <Group
                gap="xs"
                justify="center"
                p="xs"
                style={{
                  background: 'rgba(0, 0, 0, 0.7)',
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                }}
              >
                {!image.is_primary && (
                  <Button
                    size="compact-xs"
                    variant="light"
                    color="blue"
                    leftSection={<IconStar size={14} />}
                    onClick={() => handleSetPrimary(image.id)}
                  >
                    Primary
                  </Button>
                )}
                <Button
                  size="compact-xs"
                  variant="light"
                  color="red"
                  leftSection={<IconTrash size={14} />}
                  onClick={() => handleDelete(image.id)}
                >
                  Delete
                </Button>
              </Group>
            </Box>
          ))}
        </div>
      )}

      {primaryImage && (
        <Box mt="md">
          <Text fw={500} mb="xs">Preview (Primary Image):</Text>
          <Image
            src={getImageUrl(primaryImage.image_url)}
            alt="Primary Preview"
            height={250}
            fit="cover"
            radius="md"
          />
        </Box>
      )}
    </Stack>
  );
};

export default ImageUploader;
