import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { PublicRoute } from './PublicRoute';

// Lazy load pages for better performance
const AppLayout = () => import('../components/AppLayout').then(m => m.default);
const LoginPage = () => import('../pages/Auth/LoginPage').then(m => m.default);
const RegisterPage = () => import('../pages/Auth/RegisterPage').then(m => m.default);
const ListingsFeedPage = () => import('../pages/Listings/ListingsFeedPage').then(m => m.default);
const ListingDetailPage = () => import('../pages/Listings/ListingDetailPage').then(m => m.default);
const MyListingsPage = () => import('../pages/Listings/MyListingsPage').then(m => m.default);
const CreateListingPage = () => import('../pages/Listings/CreateListingPage').then(m => m.default);
const EditListingPage = () => import('../pages/Listings/EditListingPage').then(m => m.default);
const MyBookingsPage = () => import('../pages/Bookings/MyBookingsPage').then(m => m.default);
const BookingDetailPage = () => import('../pages/Bookings/BookingDetailPage').then(m => m.default);

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
