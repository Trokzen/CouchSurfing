import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Divider,
  SimpleGrid,
  Modal,
  Textarea
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { DatePickerInput } from '@mantine/dates';
import { IconCalendar, IconUser, IconHome } from '@tabler/icons-react';
import { listingApi } from '../../api/listings';
import { bookingApi } from '../../api/bookings';
import type { Listing, BookingCreate } from '../../types';
import { useAuth } from '../../contexts/AuthContext';

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [listing, setListing] = useState<Listing | null>(null);
  const [loading, setLoading] = useState(true);
  const [bookingModalOpened, setBookingModalOpened] = useState(false);
  const [checkIn, setCheckIn] = useState<Date | null>(null);
  const [checkOut, setCheckOut] = useState<Date | null>(null);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isOwner = user?.role === 'host' && listing && listing.host_id === user.id;

  const fetchListing = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await listingApi.getListingById(parseInt(id));
      setListing(data);
    } catch (error) {
      console.error('Failed to fetch listing:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load listing details',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListing();
  }, [id]);

  const handleCreateBooking = async () => {
    if (!checkIn || !checkOut || !id) {
      showNotification({
        title: 'Invalid dates',
        message: 'Please select check-in and check-out dates',
        color: 'orange',
      });
      return;
    }

    if (checkIn >= checkOut) {
      showNotification({
        title: 'Invalid date range',
        message: 'Check-out date must be after check-in date',
        color: 'orange',
      });
      return;
    }

    setSubmitting(true);
    try {
      const bookingData: BookingCreate = {
        listing_id: parseInt(id),
        start_date: checkIn.toISOString().split('T')[0],
        end_date: checkOut.toISOString().split('T')[0],
        message: message || undefined,
      };

      await bookingApi.createBooking(bookingData);
      
      showNotification({
        title: 'Booking created!',
        message: 'Your booking request has been sent to the host',
        color: 'green',
      });
      
      setBookingModalOpened(false);
      navigate('/bookings');
    } catch (error: any) {
      console.error('Failed to create booking:', error);
      showNotification({
        title: 'Booking failed',
        message: error.response?.data?.detail || 'Failed to create booking',
        color: 'red',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditListing = () => {
    navigate(`/listings/${id}/edit`);
  };

  const handleDeleteListing = async () => {
    if (!id || !window.confirm('Are you sure you want to delete this listing?')) return;
    
    try {
      await listingApi.deleteListing(parseInt(id));
      showNotification({
        title: 'Listing deleted',
        message: 'The listing has been successfully deleted',
        color: 'green',
      });
      navigate('/my-listings');
    } catch (error) {
      console.error('Failed to delete listing:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to delete listing',
        color: 'red',
      });
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
    return (
      <Container size="lg" my="md">
        <Title order={2}>Listing not found</Title>
        <Button mt="md" onClick={() => navigate('/listings')}>
          Back to listings
        </Button>
      </Container>
    );
  }

  return (
    <Container size="lg" my="md">
      <Stack gap="md">
        {/* Header */}
        <Group justify="space-between">
          <Title order={2}>{listing.title}</Title>
          {!listing.is_active && (
            <Badge color="gray" variant="dot">Inactive</Badge>
          )}
        </Group>

        {/* Owner Actions */}
        {isOwner && (
          <Card withBorder shadow="sm" p="md">
            <Group justify="space-between">
              <Text fw={500}>Host Controls</Text>
              <Group>
                <Button variant="outline" onClick={handleEditListing}>
                  Edit Listing
                </Button>
                <Button color="red" variant="outline" onClick={handleDeleteListing}>
                  Delete Listing
                </Button>
              </Group>
            </Group>
          </Card>
        )}

        {/* Main Info */}
        <Card withBorder shadow="sm" p="lg">
          <Stack gap="md">
            <Group>
              <IconHome size={20} />
              <Text fw={500}>Location</Text>
            </Group>
            <Text ml={28}>{listing.address}, {listing.city}</Text>
            
            <Divider />
            
            <Group>
              <IconUser size={20} />
              <Text fw={500}>Capacity</Text>
            </Group>
            <Text ml={28}>{listing.capacity} guests maximum</Text>
            
            <Divider />
            
            <Text fw={500}>Description</Text>
            <Text>{listing.description}</Text>
            
            <Divider />
            
            <Text fw={500}>Amenities</Text>
            {listing.amenities && listing.amenities.length > 0 ? (
              <SimpleGrid cols={{ base: 2, sm: 3 }} spacing="xs">
                {listing.amenities.map((amenity) => (
                  <Badge key={amenity} variant="light">
                    {amenity}
                  </Badge>
                ))}
              </SimpleGrid>
            ) : (
              <Text c="dimmed">No amenities listed</Text>
            )}
          </Stack>
        </Card>

        {/* Booking Section (for guests) */}
        {!isOwner && isAuthenticated && user?.role === 'guest' && listing.is_active && (
          <Card withBorder shadow="sm" p="lg">
            <Group mb="md">
              <IconCalendar size={20} />
              <Title order={4}>Book this place</Title>
            </Group>
            <Button onClick={() => setBookingModalOpened(true)}>
              Request to Book
            </Button>
          </Card>
        )}

        {!isAuthenticated && (
          <Card withBorder shadow="sm" p="lg">
            <Text c="dimmed">Please log in to book this place</Text>
            <Button component="a" href="/login" mt="md">
              Log In
            </Button>
          </Card>
        )}
      </Stack>

      {/* Booking Modal */}
      <Modal
        opened={bookingModalOpened}
        onClose={() => setBookingModalOpened(false)}
        title="Request to Book"
        size="md"
      >
        <Stack gap="md">
          <DatePickerInput
            label="Check-in Date"
            placeholder="Select date"
            value={checkIn}
            onChange={setCheckIn}
            required
          />
          <DatePickerInput
            label="Check-out Date"
            placeholder="Select date"
            value={checkOut}
            onChange={setCheckOut}
            required
          />
          <Textarea
            label="Message to Host (optional)"
            placeholder="Introduce yourself and explain why you're traveling..."
            value={message}
            onChange={(e) => setMessage(e.currentTarget.value)}
            minRows={3}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setBookingModalOpened(false)}>
              Cancel
            </Button>
            <Button loading={submitting} onClick={handleCreateBooking}>
              Submit Request
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
