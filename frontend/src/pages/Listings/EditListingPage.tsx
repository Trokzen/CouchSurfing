import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Title, 
  Card, 
  Group, 
  Button, 
  Stack,
  LoadingOverlay,
  Box,
  TextInput,
  Textarea,
  NumberInput,
  Switch
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { showNotification } from '@mantine/notifications';
import { listingApi } from '../../api/listings';
import type { Listing, ListingUpdate } from '../../types';

export default function EditListingPage() {
  const navigate = useNavigate();
  const [listing, setListing] = useState<Listing | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

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

  useEffect(() => {
    const fetchListing = async () => {
      const pathParts = window.location.pathname.split('/');
      const id = pathParts[pathParts.length - 2];
      
      if (!id) {
        showNotification({
          title: 'Error',
          message: 'Listing ID not found',
          color: 'red',
        });
        navigate('/my-listings');
        return;
      }

      setLoading(true);
      try {
        const data = await listingApi.getListingById(parseInt(id));
        setListing(data);
        form.setValues({
          title: data.title,
          description: data.description,
          city: data.city,
          address: data.address,
          capacity: data.capacity,
          amenities: data.amenities.join(', '),
          is_active: data.is_active,
        });
      } catch (error) {
        console.error('Failed to fetch listing:', error);
        showNotification({
          title: 'Error',
          message: 'Failed to load listing',
          color: 'red',
        });
        navigate('/my-listings');
      } finally {
        setLoading(false);
      }
    };

    fetchListing();
  }, []);

  const handleSubmit = async (values: typeof form.values) => {
    if (!listing) return;

    setSubmitting(true);
    try {
      const amenitiesArray = values.amenities
        .split(',')
        .map((a) => a.trim())
        .filter((a) => a.length > 0);

      const updateData: ListingUpdate = {};
      if (values.title !== listing.title) updateData.title = values.title;
      if (values.description !== listing.description) updateData.description = values.description;
      if (values.city !== listing.city) updateData.city = values.city;
      if (values.address !== listing.address) updateData.address = values.address;
      if (values.capacity !== listing.capacity) updateData.capacity = values.capacity;
      if (values.amenities !== listing.amenities.join(', ')) updateData.amenities = amenitiesArray;
      if (values.is_active !== listing.is_active) updateData.is_active = values.is_active;

      await listingApi.updateListing(listing.id, updateData);
      
      showNotification({
        title: 'Listing updated',
        message: 'The listing has been successfully updated',
        color: 'green',
      });
      
      navigate('/my-listings');
    } catch (error: any) {
      console.error('Failed to update listing:', error);
      showNotification({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to update listing',
        color: 'red',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Container size="lg" my="md">
        <Box pos="relative" style={{ minHeight: '400px' }}>
          <LoadingOverlay visible={true} />
        </Box>
      </Container>
    );
  }

  if (!listing) {
    return null;
  }

  return (
    <Container size="lg" my="md">
      <Title order={2} mb="md">Edit Listing</Title>

      <Card withBorder shadow="sm" p="lg">
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
              placeholder="Describe your place..."
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
              placeholder="Full address"
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
              placeholder="wifi, kitchen, washing_machine, air_conditioning"
              {...form.getInputProps('amenities')}
            />

            <Switch
              label="Active (visible to guests)"
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
                Update Listing
              </Button>
            </Group>
          </Stack>
        </form>
      </Card>
    </Container>
  );
}
