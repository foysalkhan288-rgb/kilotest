import { ReactNode } from "react";
import { AppShell, NavLink, Group, Text, Button, Burger } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { NavLink as RouterNavLink, Outlet, useNavigate, Navigate } from "react-router-dom";
import { getAccessToken } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface NavItem {
  label: string;
  to: string;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Contacts", to: "/contacts" },
  { label: "Pipelines", to: "/pipelines" },
  { label: "Forms", to: "/forms" },
  { label: "Pages", to: "/pages" },
  { label: "Email", to: "/email" },
  { label: "Inbox", to: "/inbox" },
  { label: "Calendar", to: "/calendar" },
  { label: "Workflows", to: "/workflows" },
  { label: "Reviews", to: "/reviews" },
];

export default function Layout() {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const { logout, workspace } = useAuth();

  if (!getAccessToken()) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: "sm", collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header p="xs">
        <Group justify="space-between" sx={{ height: "100%" }}>
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Text fw={700}>GoHighLevel Clone</Text>
            {workspace && (
              <Text size="sm" color="dimmed">
                {workspace.name}
              </Text>
            )}
          </Group>
          <Button variant="default" size="xs" onClick={handleLogout}>
            Logout
          </Button>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            component={RouterNavLink}
            to={item.to}
            label={item.label}
            end={item.to === "/dashboard"}
          />
        ))}
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  if (!getAccessToken()) {
    return <RouterNavLink to="/login" replace />;
  }
  return <>{children}</>;
}
