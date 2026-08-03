import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  TextInput,
  PasswordInput,
  Button,
  Paper,
  Title,
  Text,
  Stack,
  Anchor,
  Alert,
} from "@mantine/core";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface LoginForm {
  email: string;
  password: string;
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>();

  const onSubmit = async (values: LoginForm) => {
    setError(null);
    try {
      await login(values);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError("Invalid email or password. Please try again.");
    }
  };

  return (
    <Paper withBorder shadow="md" p={30} mt={30} radius="md" w={400} mx="auto">
      <Title order={2} mb="md" ta="center">
        Sign in
      </Title>
      {error && (
        <Alert color="red" mb="md">
          {error}
        </Alert>
      )}
      <form onSubmit={handleSubmit(onSubmit)}>
        <Stack>
          <TextInput
            label="Email"
            placeholder="you@example.com"
            required
            {...register("email", { required: "Email is required" })}
            error={errors.email?.message}
          />
          <PasswordInput
            label="Password"
            placeholder="Your password"
            required
            {...register("password", { required: "Password is required" })}
            error={errors.password?.message}
          />
          <Button type="submit" loading={isSubmitting} fullWidth>
            Login
          </Button>
          <Text size="sm" align="center">
            No account?{" "}
            <Anchor component={Link} to="/register">
              Register
            </Anchor>
          </Text>
        </Stack>
      </form>
    </Paper>
  );
}
