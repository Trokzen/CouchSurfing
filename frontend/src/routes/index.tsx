import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { PublicRoute } from './PublicRoute';

// Import pages directly (not lazy-loaded for simplicity)
import AppLayout from '../components/AppLayout';
import LoginPage from '../pages/Auth/LoginPage';
import RegisterPage from '../pages/Auth/RegisterPage';
import ListingsFeedPage from '../pages/Listings/ListingsFeedPage';
import ListingDetailPage from '../pages/Listings/ListingDetailPage';
import MyListingsPage from '../pages/Listings/MyListingsPage';
import CreateListingPage from '../pages/Listings/CreateListingPage';
import EditListingPage from '../pages/Listings/EditListingPage';
import MyBookingsPage from '../pages/Bookings/MyBookingsPage';
import BookingDetailPage from '../pages/Bookings/BookingDetailPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/listings" replace />,
      },
      {
        path: 'listings',
        element: <ListingsFeedPage />,
      },
      {
        path: 'listings/:id',
        element: <ListingDetailPage />,
      },
      {
        path: 'my-listings',
        element: (
          <ProtectedRoute requiredRole="host">
            <MyListingsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'listings/create',
        element: (
          <ProtectedRoute requiredRole="host">
            <CreateListingPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'listings/:id/edit',
        element: (
          <ProtectedRoute requiredRole="host">
            <EditListingPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'bookings',
        element: (
          <ProtectedRoute>
            <MyBookingsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'bookings/:id',
        element: (
          <ProtectedRoute>
            <BookingDetailPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: '/login',
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
  },
  {
    path: '/register',
    element: (
      <PublicRoute>
        <RegisterPage />
      </PublicRoute>
    ),
  },
]);
