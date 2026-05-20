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
  Timeline
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { bookingApi } from '../../api/bookings';
import type { Booking, BookingStatus } from '../../types';
import { useAuth } from '../../contexts/AuthContext';

const statusColors: Record<BookingStatus, string> = {
  new: 'gray',
  pending: 'yellow',
  confirmed: 'green',
  rejected: 'red',
  cancelled: 'orange',
  completed: 'blue',
};

const statusLabels: Record<BookingStatus, string> = {
  new: 'New Request',
  pending: 'Pending Host Review',
  confirmed: 'Confirmed by Host',
  rejected: 'Rejected by Host',
  cancelled: 'Cancelled',
  completed: 'Completed',
};

export default function BookingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const isHost = user?.role === 'host';
  const isGuest = user?.role === 'guest';

  const fetchBooking = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await bookingApi.getBookingById(parseInt(id));
      setBooking(data);
    } catch (error) {
      console.error('Failed to fetch booking:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load booking details',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooking();
  }, [id]);

  const handleAction = async (action: 'confirm' | 'reject' | 'cancel') => {
    if (!booking) return;

    setSubmitting(true);
    try {
      switch (action) {
        case 'confirm':
          await bookingApi.confirmBooking(booking.id);
          showNotification({
            title: 'Booking confirmed',
            message: 'The booking has been confirmed',
            color: 'green',
          });
          break;
        case 'reject':
          await bookingApi.rejectBooking(booking.id);
          showNotification({
            title: 'Booking rejected',
            message: 'The booking has been rejected',
            color: 'red',
          });
          break;
        case 'cancel':
          await bookingApi.cancelBooking(booking.id);
          showNotification({
            title: 'Booking cancelled',
            message: 'The booking has been cancelled',
            color: 'orange',
          });
          break;
      }
      fetchBooking();
    } catch (error: any) {
      console.error('Failed to perform action:', error);
      showNotification({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to perform action',
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

  if (!booking) {
    return (
      <Container size="lg" my="md">
        <Title order={2}>Booking not found</Title>
        <Button mt="md" onClick={() => navigate('/bookings')}>
          Back to bookings
        </Button>
      </Container>
    );
  }

  const canConfirm = isHost && booking.status === 'pending';
  const canReject = isHost && booking.status === 'pending';
  const canCancel = isGuest && (booking.status === 'pending' || booking.status === 'confirmed');

  return (
    <Container size="lg" my="md">
      <Stack gap="md">
        {/* Header */}
        <Group justify="space-between">
          <Title order={2}>Booking Details</Title>
          <Badge 
            size="lg" 
            color={statusColors[booking.status]} 
            variant="dot"
          >
            {statusLabels[booking.status]}
          </Badge>
        </Group>

        {/* Booking Info */}
        <Card withBorder shadow="sm" p="lg">
          <Stack gap="md">
            <Group>
              <Text fw={500}>Listing:</Text>
              <Text>{booking.listing_title}</Text>
            </Group>
            
            <Divider />
            
            <Group>
              <Text fw={500}>Location:</Text>
              <Text>{booking.listing_city}</Text>
            </Group>
            
            <Divider />
            
            <Group>
              <Text fw={500}>Check-in:</Text>
              <Text>{booking.start_date}</Text>
            </Group>
            
            <Divider />
            
            <Group>
              <Text fw={500}>Check-out:</Text>
              <Text>{booking.end_date}</Text>
            </Group>
            
            <Divider />
            
            <Group>
              <Text fw={500}>Guest:</Text>
              <Text>{booking.guest_name}</Text>
            </Group>
            
            {booking.message && (
              <>
                <Divider />
                <Group align="flex-start">
                  <Text fw={500}>Message:</Text>
                  <Text>{booking.message}</Text>
                </Group>
              </>
            )}
            
            <Divider />
            
            <Group>
              <Text fw={500}>Created:</Text>
              <Text>{new Date(booking.created_at).toLocaleString()}</Text>
            </Group>
            
            <Divider />
            
            <Group>
              <Text fw={500}>Last Updated:</Text>
              <Text>{new Date(booking.updated_at).toLocaleString()}</Text>
            </Group>
          </Stack>
        </Card>

        {/* Actions */}
        {(canConfirm || canReject || canCancel) && (
          <Card withBorder shadow="sm" p="lg">
            <Title order={4} mb="md">Actions</Title>
            <Group>
              {canConfirm && (
                <Button
                  color="green"
                  loading={submitting}
                  onClick={() => handleAction('confirm')}
                >
                  Confirm Booking
                </Button>
              )}
              {canReject && (
                <Button
                  color="red"
                  variant="outline"
                  loading={submitting}
                  onClick={() => handleAction('reject')}
                >
                  Reject Booking
                </Button>
              )}
              {canCancel && (
                <Button
                  color="orange"
                  variant="outline"
                  loading={submitting}
                  onClick={() => handleAction('cancel')}
                >
                  Cancel Booking
                </Button>
              )}
            </Group>
          </Card>
        )}

        {/* Status Timeline */}
        <Card withBorder shadow="sm" p="lg">
          <Title order={4} mb="md">Booking History</Title>
          <Timeline active={3} bulletSize={24} lineWidth={2}>
            <Timeline.Item
              title="Booking Created"
              bulletColor={statusColors.new}
            >
              <Text size="sm" c="dimmed">
                {new Date(booking.created_at).toLocaleString()}
              </Text>
              <Text size="xs" c="dimmed">
                Initial booking request submitted
              </Text>
            </Timeline.Item>
            
            {booking.status !== 'new' && (
              <Timeline.Item
                title={statusLabels.pending}
                bulletColor={statusColors.pending}
              >
                <Text size="sm" c="dimmed">
                  Pending host review
                </Text>
              </Timeline.Item>
            )}
            
            {booking.status === 'confirmed' && (
              <Timeline.Item
                title={statusLabels.confirmed}
                bulletColor={statusColors.confirmed}
              >
                <Text size="sm" c="dimmed">
                  Host confirmed the booking
                </Text>
              </Timeline.Item>
            )}
            
            {booking.status === 'rejected' && (
              <Timeline.Item
                title={statusLabels.rejected}
                bulletColor={statusColors.rejected}
              >
                <Text size="sm" c="dimmed">
                  Host rejected the booking
                </Text>
              </Timeline.Item>
            )}
            
            {booking.status === 'cancelled' && (
              <Timeline.Item
                title={statusLabels.cancelled}
                bulletColor={statusColors.cancelled}
              >
                <Text size="sm" c="dimmed">
                  Booking was cancelled
                </Text>
              </Timeline.Item>
            )}
            
            {booking.status === 'completed' && (
              <>
                <Timeline.Item
                  title={statusLabels.confirmed}
                  bulletColor={statusColors.confirmed}
                >
                  <Text size="sm" c="dimmed">
                    Host confirmed the booking
                  </Text>
                </Timeline.Item>
                <Timeline.Item
                  title={statusLabels.completed}
                  bulletColor={statusColors.completed}
                >
                  <Text size="sm" c="dimmed">
                    Stay completed successfully
                  </Text>
                </Timeline.Item>
              </>
            )}
          </Timeline>
        </Card>

        {/* Navigation */}
        <Group>
          <Button variant="outline" onClick={() => navigate('/bookings')}>
            Back to Bookings
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}
