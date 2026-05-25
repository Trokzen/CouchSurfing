import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Title, 
  Card, 
  Group, 
  Button, 
  Stack,
  TextInput,
  Textarea,
  NumberInput,
  Switch
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';
import { listingApi } from '../../api/listings';
import type { ListingCreate } from '../../types';
import ImageUploader from '../../components/ImageUploader';

export default function CreateListingPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [createdListingId, setCreatedListingId] = useState<number | null>(null);

  const form = useForm({
    initialValues: {
      title: '',
      description: '',
      city: '',
      address: '',
      capacity: 1,
      amenities: '',
      is_active: true,
    },
    validate: {
      title: (value) => (value.length >= 3 ? null : 'Title must be at least 3 characters'),
      description: (value) => (value.length >= 10 ? null : 'Description must be at least 10 characters'),
      city: (value) => (value.length >= 2 ? null : 'City is required'),
      address: (value) => (value.length >= 5 ? null : 'Address is required'),
      capacity: (value) => (value >= 1 && value <= 20 ? null : 'Capacity must be between 1 and 20'),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setSubmitting(true);
    try {
      const amenitiesArray = values.amenities
        .split(',')
        .map((a) => a.trim())
        .filter((a) => a.length > 0);

      const listingData: ListingCreate = {
        title: values.title,
        description: values.description,
        city: values.city,
        address: values.address,
        capacity: values.capacity,
        amenities: amenitiesArray,
        is_active: values.is_active,
      };

      const createdListing = await listingApi.createListing(listingData);
      setCreatedListingId(createdListing.id);
      
      showNotification({
        title: 'Listing created',
        message: 'Your listing has been successfully created. You can now add photos.',
        color: 'green',
      });
    } catch (error: any) {
      console.error('Failed to create listing:', error);
      showNotification({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to create listing',
        color: 'red',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleImagesComplete = () => {
    navigate('/my-listings');
  };

  return (
    <Container size="lg" my="md">
      <Title order={2} mb="md">Create New Listing</Title>

      <Card withBorder shadow="sm" p="lg">
        {!createdListingId ? (
          <form onSubmit={form.onSubmit(handleSubmit)}>
            <Stack gap="md">
              <TextInput
                label="Title"
                placeholder="e.g., Cozy Studio in City Center"
                {...form.getInputProps('title')}
                required
              />

              <Textarea
                label="Description"
                placeholder="Describe your place in detail. What makes it special? What can guests expect?"
                {...form.getInputProps('description')}
                minRows={4}
                required
              />

              <TextInput
                label="City"
                placeholder="e.g., Moscow"
                {...form.getInputProps('city')}
                required
              />

              <TextInput
                label="Address"
                placeholder="Full address (street, building, apartment)"
                {...form.getInputProps('address')}
                required
              />

              <NumberInput
                label="Capacity (number of guests)"
                min={1}
                max={20}
                {...form.getInputProps('capacity')}
                required
              />

              <TextInput
                label="Amenities (comma-separated)"
                placeholder="wifi, kitchen, washing_machine, air_conditioning, heating"
                {...form.getInputProps('amenities')}
                description="List the amenities available at your place"
              />

              <Switch
                label="Active (visible to guests immediately)"
                {...form.getInputProps('is_active', { type: 'checkbox' })}
              />

              <Group justify="flex-end" mt="md">
                <Button
                  variant="default"
                  onClick={() => navigate('/my-listings')}
                  type="button"
                >
                  Cancel
                </Button>
                <Button loading={submitting} type="submit">
                  Create Listing
                </Button>
              </Group>
            </Stack>
          </form>
        ) : (
          <Stack gap="md">
            <Title order={3}>Add Photos to Your Listing</Title>
            <ImageUploader 
              listingId={createdListingId} 
              onImagesChange={handleImagesComplete}
            />
            <Group justify="flex-end" mt="md">
              <Button
                variant="default"
                onClick={() => navigate('/my-listings')}
              >
                Skip and Finish
              </Button>
            </Group>
          </Stack>
        )}
      </Card>
    </Container>
  );
}
