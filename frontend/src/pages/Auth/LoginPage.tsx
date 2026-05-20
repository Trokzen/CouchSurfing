import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from '@mantine/form';
import { Button, TextInput, PasswordInput, Paper, Title, Text, Container, Group, Box, Divider } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useAuth } from '../../contexts/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: {
      email: '',
      password: '',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      password: (value) => (value.length >= 1 ? null : 'Password is required'),
    },
  });

  const handleSubmit = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.email, values.password);
      showNotification({
        title: 'Welcome back!',
        message: 'You have successfully logged in',
        color: 'green',
      });
      navigate('/listings');
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed. Please check your credentials.';
      showNotification({
        title: 'Login failed',
        message: errorMessage.includes('Incorrect') ? 'Invalid email or password' : errorMessage,
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={420} my={40}>
      <Title ta="center" mt="md">
        Welcome to CouchSurfing!
      </Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        Don't have an account yet?{' '}
        <Link to="/register" style={{ textDecoration: 'none' }}>
          Create account
        </Link>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <TextInput
            label="Email"
            placeholder="your@email.com"
            required
            type="email"
            {...form.getInputProps('email')}
          />
          <PasswordInput
            label="Password"
            placeholder="Your password"
            required
            mt="md"
            {...form.getInputProps('password')}
          />
          <Group justify="space-between" mt="lg">
            <Button loading={loading} type="submit" fullWidth>
              Sign in
            </Button>
          </Group>
        </form>
      </Paper>
    </Container>
  );
}
