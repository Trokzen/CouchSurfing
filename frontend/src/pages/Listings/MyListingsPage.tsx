import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Title, 
  Text, 
  Card, 
  Group, 
  Badge, 
  Button, 
  Stack,
  LoadingOverlay,
  Box,
  SimpleGrid,
  ActionIcon,
  Space,
  Modal,
  TextInput,
  Textarea,
  NumberInput,
  Switch
} from '@mantine/core';
import { IconPlus, IconEdit, IconTrash } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { listingApi } from '../../api/listings';
import type { Listing, ListingUpdate } from '../../types';
import { useAuth } from '../../contexts/AuthContext';

export default function MyListingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModalOpened, setEditModalOpened] = useState(false);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    city: '',
    address: '',
    capacity: 1,
    amenities: '',
    is_active: true,
  });

  const fetchListings = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const data = await listingApi.getHostListings(user.id, true);
      setListings(data);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load your listings',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [user?.id]);

  const handleCreateListing = () => {
    setSelectedListing(null);
    setFormData({
      title: '',
      description: '',
      city: '',
      address: '',
      capacity: 1,
      amenities: '',
      is_active: true,
    });
    setEditModalOpened(true);
  };

  const handleEditListing = (listing: Listing) => {
    setSelectedListing(listing);
    setFormData({
      title: listing.title,
      description: listing.description,
      city: listing.city,
      address: listing.address,
      capacity: listing.capacity,
      amenities: listing.amenities.join(', '),
      is_active: listing.is_active,
    });
    setEditModalOpened(true);
  };

  const handleDeleteListing = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this listing?')) return;
    
    try {
      await listingApi.deleteListing(id);
      showNotification({
        title: 'Listing deleted',
        message: 'The listing has been successfully deleted',
        color: 'green',
      });
      fetchListings();
    } catch (error) {
      console.error('Failed to delete listing:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to delete listing',
        color: 'red',
      });
    }
  };

  const handleSubmit = async () => {
    try {
      const amenitiesArray = formData.amenities
        .split(',')
        .map((a) => a.trim())
        .filter((a) => a.length > 0);

      const listingData = {
        title: formData.title,
        description: formData.description,
        city: formData.city,
        address: formData.address,
        capacity: formData.capacity,
        amenities: amenitiesArray,
        is_active: formData.is_active,
      };

      if (selectedListing) {
        // Update existing listing
        const updateData: ListingUpdate = {};
        if (formData.title !== selectedListing.title) updateData.title = formData.title;
        if (formData.description !== selectedListing.description) updateData.description = formData.description;
        if (formData.city !== selectedListing.city) updateData.city = formData.city;
        if (formData.address !== selectedListing.address) updateData.address = formData.address;
        if (formData.capacity !== selectedListing.capacity) updateData.capacity = formData.capacity;
        if (formData.amenities !== selectedListing.amenities.join(', ')) updateData.amenities = amenitiesArray;
        if (formData.is_active !== selectedListing.is_active) updateData.is_active = formData.is_active;

        await listingApi.updateListing(selectedListing.id, updateData);
        showNotification({
          title: 'Listing updated',
          message: 'The listing has been successfully updated',
          color: 'green',
        });
      } else {
        // Create new listing
        await listingApi.createListing(listingData);
        showNotification({
          title: 'Listing created',
          message: 'Your listing has been successfully created',
          color: 'green',
        });
      }

      setEditModalOpened(false);
      fetchListings();
    } catch (error: any) {
      console.error('Failed to save listing:', error);
      showNotification({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to save listing',
        color: 'red',
      });
    }
  };

  const getStatusBadge = (listing: Listing) => {
    if (listing.is_active) {
      return <Badge color="green" variant="dot">Active</Badge>;
    }
    return <Badge color="gray" variant="dot">Inactive</Badge>;
  };

  return (
    <Container size="xl" my="md">
      <Group justify="space-between" mb="md">
        <Title order={2}>My Listings</Title>
        <Button leftSection={<IconPlus size={18} />} onClick={handleCreateListing}>
          Create New Listing
        </Button>
      </Group>

      <Box pos="relative">
        <LoadingOverlay visible={loading} />
        
        {listings.length === 0 && !loading ? (
          <Card withBorder shadow="sm" p="lg">
            <Text ta="center" c="dimmed">
              You don't have any listings yet. Create your first listing to start hosting!
            </Text>
            <Button fullWidth mt="md" onClick={handleCreateListing}>
              Create Your First Listing
            </Button>
          </Card>
        ) : (
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            {listings.map((listing) => (
              <Card key={listing.id} withBorder shadow="sm" padding="lg">
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Title order={4}>{listing.title}</Title>
                    {getStatusBadge(listing)}
                  </Group>
                  
                  <Text size="sm" c="dimmed">{listing.city}</Text>
                  <Text size="sm">Capacity: {listing.capacity} guests</Text>
                  <Text size="sm" lineClamp={2}>{listing.description}</Text>
                  
                  {listing.amenities && listing.amenities.length > 0 && (
                    <Group gap="xs">
                      {listing.amenities.slice(0, 3).map((amenity) => (
                        <Badge key={amenity} variant="light" size="sm">
                          {amenity}
                        </Badge>
                      ))}
                      {listing.amenities.length > 3 && (
                        <Text size="xs" c="dimmed">+{listing.amenities.length - 3} more</Text>
                      )}
                    </Group>
                  )}
                  
                  <Space h="xs" />
                  
                  <Group justify="flex-end">
                    <ActionIcon
                      variant="default"
                      onClick={() => navigate(`/listings/${listing.id}`)}
                      title="View details"
                    >
                      <IconEdit size={18} />
                    </ActionIcon>
                    <ActionIcon
                      variant="default"
                      onClick={() => handleEditListing(listing)}
                      title="Edit"
                    >
                      <IconEdit size={18} />
                    </ActionIcon>
                    <ActionIcon
                      color="red"
                      variant="default"
                      onClick={() => handleDeleteListing(listing.id)}
                      title="Delete"
                    >
                      <IconTrash size={18} />
                    </ActionIcon>
                  </Group>
                </Stack>
              </Card>
            ))}
          </SimpleGrid>
        )}
      </Box>

      {/* Create/Edit Modal */}
      <Modal
        opened={editModalOpened}
        onClose={() => setEditModalOpened(false)}
        title={selectedListing ? 'Edit Listing' : 'Create New Listing'}
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="Title"
            placeholder="e.g., Cozy Studio in City Center"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.currentTarget.value })}
            required
          />
          
          <Textarea
            label="Description"
            placeholder="Describe your place..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.currentTarget.value })}
            minRows={4}
            required
          />
          
          <TextInput
            label="City"
            placeholder="e.g., Moscow"
            value={formData.city}
            onChange={(e) => setFormData({ ...formData, city: e.currentTarget.value })}
            required
          />
          
          <TextInput
            label="Address"
            placeholder="Full address"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.currentTarget.value })}
            required
          />
          
          <NumberInput
            label="Capacity (number of guests)"
            min={1}
            max={20}
            value={formData.capacity}
            onChange={(val) => setFormData({ ...formData, capacity: typeof val === 'number' ? val : 1 })}
            required
          />
          
          <TextInput
            label="Amenities (comma-separated)"
            placeholder="wifi, kitchen, washing_machine, air_conditioning"
            value={formData.amenities}
            onChange={(e) => setFormData({ ...formData, amenities: e.currentTarget.value })}
          />
          
          <Switch
            label="Active (visible to guests)"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.currentTarget.checked })}
          />
          
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setEditModalOpened(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {selectedListing ? 'Update Listing' : 'Create Listing'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
