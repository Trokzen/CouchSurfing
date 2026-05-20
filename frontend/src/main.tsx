import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { DatesProvider } from '@mantine/dates';
import { AuthProvider } from './contexts/AuthContext';
import { router } from './routes';

import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MantineProvider defaultColorScheme="auto">
      <DatesProvider settings={{ locale: 'en' }}>
        <Notifications position="top-right" />
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </DatesProvider>
    </MantineProvider>
  </React.StrictMode>
);
