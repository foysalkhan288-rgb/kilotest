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

interface RegisterForm {
  name: string;
  email: string;
  password: string;
  workspace_name: string;
}

export default function Register() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>();

  const onSubmit = async (values: RegisterForm) => {
    setError(null);
    try {
      await registerUser(values);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError("Registration failed. Please try again.");
    }
  };

  return (
    <Paper withBorder shadow="md" p={30} mt={30} radius="md" w={400} mx="auto">
      <Title order={2} mb="md" align="center">
        Create account
      </Title>
      {error && (
        <Alert color="red" mb="md">
          {error}
        </Alert>
      )}
      <form onSubmit={handleSubmit(onSubmit)}>
        <Stack>
          <TextInput
            label="Name"
            placeholder="Jane Doe"
            required
            {...register("name", { required: "Name is required" })}
            error={errors.name?.message}
          />
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
          <TextInput
            label="Workspace name"
            placeholder="Acme Co"
            required
            {...register("workspace_name", {
              required: "Workspace name is required",
            })}
            error={errors.workspace_name?.message}
          />
          <Button type="submit" loading={isSubmitting} fullWidth>
            Register
          </Button>
          <Text size="sm" align="center">
            Already have an account?{" "}
            <Anchor component={Link} to="/login">
              Sign in
            </Anchor>
          </Text>
        </Stack>
      </form>
    </Paper>
  );
}
