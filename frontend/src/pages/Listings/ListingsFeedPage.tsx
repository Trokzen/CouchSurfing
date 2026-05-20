import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Title, 
  SimpleGrid, 
  Card, 
  Text, 
  Group, 
  Badge, 
  Button, 
  Stack,
  LoadingOverlay,
  Box,
  TextInput,
  NumberInput
} from '@mantine/core';
import { IconSearch, IconCalendar } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import { listingApi } from '../../api/listings';
import type { Listing, PaginatedResponse } from '../../types';
import { DatePickerInput } from '@mantine/dates';

export default function ListingsFeedPage() {
  const navigate = useNavigate();
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchCity, setSearchCity] = useState('');
  const [checkIn, setCheckIn] = useState<Date | null>(null);
  const [checkOut, setCheckOut] = useState<Date | null>(null);
  const [minCapacity, setMinCapacity] = useState<number | undefined>(undefined);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const filters: Record<string, string | number> = {
        page: 1,
        size: 20,
      };
      
      if (searchCity) filters.city = searchCity;
      if (checkIn) filters.check_in = checkIn.toISOString().split('T')[0];
      if (checkOut) filters.check_out = checkOut.toISOString().split('T')[0];
      if (minCapacity !== undefined) filters.min_capacity = minCapacity;

      const response: PaginatedResponse<Listing> = await listingApi.searchListings(filters as any);
      setListings(response.items || []);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
      showNotification({
        title: 'Error',
        message: 'Failed to load listings',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, []);

  const handleSearch = () => {
    fetchListings();
  };

  return (
    <Container size="xl" my="md">
      <Title order={2} mb="md">Browse Listings</Title>
      
      {/* Filters */}
      <Card withBorder shadow="sm" p="md" mb="md">
        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
          <TextInput
            label="City"
            placeholder="Search by city..."
            value={searchCity}
            onChange={(e) => setSearchCity(e.currentTarget.value)}
            leftSection={<IconSearch style={{ width: 18, height: 18 }} />}
          />
          <DatePickerInput
            label="Check-in Date"
            placeholder="Select date"
            value={checkIn}
            onChange={setCheckIn}
            leftSection={<IconCalendar style={{ width: 18, height: 18 }} />}
          />
          <DatePickerInput
            label="Check-out Date"
            placeholder="Select date"
            value={checkOut}
            onChange={setCheckOut}
            leftSection={<IconCalendar style={{ width: 18, height: 18 }} />}
          />
          <NumberInput
            label="Min Capacity"
            placeholder="Guests"
            value={minCapacity}
            onChange={(val) => setMinCapacity(val === null ? undefined : val)}
            min={1}
            max={20}
          />
        </SimpleGrid>
        <Group justify="flex-end" mt="md">
          <Button onClick={handleSearch}>Search</Button>
        </Group>
      </Card>

      {/* Listings Grid */}
      <Box pos="relative">
        <LoadingOverlay visible={loading} />
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="md">
          {listings.map((listing) => (
            <Card 
              key={listing.id} 
              withBorder 
              shadow="sm" 
              padding="lg" 
              radius="md"
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/listings/${listing.id}`)}
            >
              <Stack gap="sm">
                <Group justify="space-between">
                  <Title order={4}>{listing.title}</Title>
                  {!listing.is_active && (
                    <Badge color="gray" variant="dot">Inactive</Badge>
                  )}
                </Group>
                
                <Text size="sm" c="dimmed">{listing.city}</Text>
                <Text size="sm">Capacity: {listing.capacity} guests</Text>
                
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
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
        
        {listings.length === 0 && !loading && (
          <Text ta="center" c="dimmed" mt="xl">
            No listings found. Try adjusting your search criteria.
          </Text>
        )}
      </Box>
    </Container>
  );
}
