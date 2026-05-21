import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from '@mantine/form';
import { Button, TextInput, PasswordInput, Paper, Title, Text, Container, Group, Select } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useAuth } from '../../contexts/AuthContext';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: {
      email: '',
      password: '',
      confirmPassword: '',
      full_name: '',
      role: 'guest' as 'guest' | 'host',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      password: (value) => (value.length >= 8 ? null : 'Password must be at least 8 characters'),
      confirmPassword: (value, values) => (value === values.password ? null : 'Passwords do not match'),
      full_name: (value) => (value.length >= 2 ? null : 'Full name is required'),
    },
  });

  const handleSubmit = async (values: { email: string; password: string; full_name: string; role: 'guest' | 'host' }) => {
    setLoading(true);
    try {
      await register(values.email, values.password, values.full_name, values.role);
      showNotification({
        title: 'Registration successful!',
        message: 'Please log in with your credentials',
        color: 'green',
      });
      navigate('/login');
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      showNotification({
        title: 'Registration failed',
        message: errorMessage.includes('Email already') ? 'This email is already registered' : errorMessage,
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={420} my={40}>
      <Title ta="center" mt="md">
        Create your account
      </Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        Already have an account?{' '}
        <Link to="/login" style={{ textDecoration: 'none' }}>
          Sign in
        </Link>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <TextInput
            label="Full Name"
            placeholder="John Doe"
            required
            {...form.getInputProps('full_name')}
          />
          <TextInput
            label="Email"
            placeholder="your@email.com"
            required
            type="email"
            mt="md"
            {...form.getInputProps('email')}
          />
          <Select
            label="I want to"
            placeholder="Select your role"
            data={[
              { value: 'guest', label: 'Find a place to stay (Guest)' },
              { value: 'host', label: 'Offer my place (Host)' },
            ]}
            mt="md"
            {...form.getInputProps('role')}
          />
          <PasswordInput
            label="Password"
            placeholder="Your password (min 8 characters)"
            required
            mt="md"
            {...form.getInputProps('password')}
          />
          <PasswordInput
            label="Confirm Password"
            placeholder="Confirm your password"
            required
            mt="md"
            {...form.getInputProps('confirmPassword')}
          />
          <Group justify="space-between" mt="lg">
            <Button loading={loading} type="submit" fullWidth>
              Create account
            </Button>
          </Group>
        </form>
      </Paper>
    </Container>
  );
}
