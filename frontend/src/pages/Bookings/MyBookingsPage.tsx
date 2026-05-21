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
  Tabs,
  Modal,
  Textarea
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { bookingApi } from '../../api/bookings';
import type { BookingBrief, BookingStatus } from '../../types';
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
  new: 'New',
  pending: 'Pending',
  confirmed: 'Confirmed',
  rejected: 'Rejected',
  cancelled: 'Cancelled',
  completed: 'Completed',
};

export default function MyBookingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [guestBookings, setGuestBookings] = useState<BookingBrief[]>([]);
  const [hostBookings, setHostBookings] = useState<BookingBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | BookingStatus>('all');
  const [actionModalOpened, setActionModalOpened] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<BookingBrief | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [cancellationReason, setCancellationReason] = useState('');
  const [actionType, setActionType] = useState<'confirm' | 'reject' | 'cancel' | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const isHost = user?.role === 'host';

  const fetchBookings = async () => {
    setLoading(true);
    try {
      // Fetch guest bookings (as a guest)
      const guestData = await bookingApi.getMyBookings();
      setGuestBookings(guestData);

      // Fetch host bookings if user is a host
      if (isHost) {
        const hostData = await bookingApi.getHostBookings();
        setHostBookings(hostData);
      }
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load bookings',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [isHost]);

  const handleAction = async (booking: BookingBrief, type: 'confirm' | 'reject' | 'cancel') => {
    setSelectedBooking(booking);
    setActionType(type);
    setRejectionReason('');
    setCancellationReason('');
    setActionModalOpened(true);
  };

  const submitAction = async () => {
    if (!selectedBooking || !actionType) return;

    setSubmitting(true);
    try {
      switch (actionType) {
        case 'confirm':
          await bookingApi.confirmBooking(selectedBooking.id);
          showNotification({
            title: 'Booking confirmed',
            message: 'The booking has been confirmed',
            color: 'green',
          });
          break;
        case 'reject':
          await bookingApi.rejectBooking(selectedBooking.id, rejectionReason || undefined);
          showNotification({
            title: 'Booking rejected',
            message: 'The booking has been rejected',
            color: 'red',
          });
          break;
        case 'cancel':
          await bookingApi.cancelBooking(selectedBooking.id, cancellationReason || undefined);
          showNotification({
            title: 'Booking cancelled',
            message: 'The booking has been cancelled',
            color: 'orange',
          });
          break;
      }

      setActionModalOpened(false);
      fetchBookings();
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

  const getFilteredBookings = () => {
    const allBookings = [...guestBookings, ...hostBookings];
    
    if (activeTab === 'all') {
      return allBookings;
    }
    
    return allBookings.filter((booking) => booking.status === activeTab);
  };

  const getStatusBadge = (status: BookingStatus) => (
    <Badge color={statusColors[status]} variant="dot">
      {statusLabels[status]}
    </Badge>
  );

  const getAvailableActions = (booking: BookingBrief) => {
    const actions: { label: string; type: 'confirm' | 'reject' | 'cancel'; color?: string }[] = [];

    // Host actions
    if (isHost && booking.status === 'pending') {
      actions.push({ label: 'Confirm', type: 'confirm', color: 'green' });
      actions.push({ label: 'Reject', type: 'reject', color: 'red' });
    }

    // Guest actions (can cancel if pending or confirmed)
    if (!isHost && (booking.status === 'pending' || booking.status === 'confirmed')) {
      actions.push({ label: 'Cancel', type: 'cancel', color: 'orange' });
    }

    return actions;
  };

  const filteredBookings = getFilteredBookings();

  return (
    <Container size="xl" my="md">
      <Title order={2} mb="md">My Bookings</Title>

      <Tabs value={activeTab} onChange={(val) => setActiveTab(val as 'all' | BookingStatus)} mb="md">
        <Tabs.List>
          <Tabs.Tab value="all">All</Tabs.Tab>
          <Tabs.Tab value="new">New</Tabs.Tab>
          <Tabs.Tab value="pending">Pending</Tabs.Tab>
          <Tabs.Tab value="confirmed">Confirmed</Tabs.Tab>
          <Tabs.Tab value="rejected">Rejected</Tabs.Tab>
          <Tabs.Tab value="cancelled">Cancelled</Tabs.Tab>
          <Tabs.Tab value="completed">Completed</Tabs.Tab>
        </Tabs.List>
      </Tabs>

      <Box pos="relative">
        <LoadingOverlay visible={loading} />

        {filteredBookings.length === 0 && !loading ? (
          <Card withBorder shadow="sm" p="lg">
            <Text ta="center" c="dimmed">
              No bookings found
            </Text>
          </Card>
        ) : (
          <Stack gap="md">
            {filteredBookings.map((booking) => {
              const actions = getAvailableActions(booking);

              return (
                <Card key={booking.id} withBorder shadow="sm" padding="lg">
                  <Group justify="space-between">
                    <Stack gap="xs" style={{ flex: 1 }}>
                      <Group>
                        <Title order={4}>{booking.listing_title}</Title>
                        {getStatusBadge(booking.status)}
                      </Group>
                      
                      <Text size="sm" c="dimmed">
                        {booking.listing_city}
                      </Text>
                      
                      <Text size="sm">
                        <strong>Dates:</strong> {booking.start_date} → {booking.end_date}
                      </Text>

                      {booking.message && (
                        <Text size="sm" c="dimmed" mt="xs">
                          <strong>Message:</strong> {booking.message}
                        </Text>
                      )}
                    </Stack>

                    {actions.length > 0 && (
                      <Group gap="xs">
                        {actions.map((action) => (
                          <Button
                            key={action.type}
                            size="sm"
                            color={action.color}
                            variant={action.color ? 'filled' : 'outline'}
                            onClick={() => handleAction(booking, action.type)}
                          >
                            {action.label}
                          </Button>
                        ))}
                      </Group>
                    )}
                  </Group>
                  
                  <Button
                    variant="subtle"
                    size="sm"
                    mt="md"
                    onClick={() => navigate(`/bookings/${booking.id}`)}
                  >
                    View Details
                  </Button>
                </Card>
              );
            })}
          </Stack>
        )}
      </Box>

      {/* Action Modal */}
      <Modal
        opened={actionModalOpened}
        onClose={() => setActionModalOpened(false)}
        title={
          actionType === 'confirm'
            ? 'Confirm Booking'
            : actionType === 'reject'
            ? 'Reject Booking'
            : 'Cancel Booking'
        }
        size="md"
      >
        <Stack gap="md">
          {selectedBooking && (
            <>
              <Text>
                <strong>Listing:</strong> {selectedBooking.listing_title}
              </Text>
              <Text>
                <strong>Dates:</strong> {selectedBooking.start_date} → {selectedBooking.end_date}
              </Text>

              {(actionType === 'reject' || actionType === 'cancel') && (
                <Textarea
                  label={`${actionType === 'reject' ? 'Rejection' : 'Cancellation'} Reason (optional)`}
                  placeholder="Please provide a reason..."
                  value={actionType === 'reject' ? rejectionReason : cancellationReason}
                  onChange={(e) =>
                    actionType === 'reject'
                      ? setRejectionReason(e.currentTarget.value)
                      : setCancellationReason(e.currentTarget.value)
                  }
                  minRows={3}
                />
              )}

              <Group justify="flex-end" mt="md">
                <Button variant="default" onClick={() => setActionModalOpened(false)}>
                  Cancel
                </Button>
                <Button
                  loading={submitting}
                  color={actionType === 'confirm' ? 'green' : actionType === 'reject' ? 'red' : 'orange'}
                  onClick={submitAction}
                >
                  {actionType === 'confirm'
                    ? 'Confirm'
                    : actionType === 'reject'
                    ? 'Reject'
                    : 'Cancel'}
                </Button>
              </Group>
            </>
          )}
        </Stack>
      </Modal>
    </Container>
  );
}
