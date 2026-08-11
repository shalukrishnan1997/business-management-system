export type UserRole =
  | "super_admin"
  | "admin"
  | "manager"
  | "accountant"
  | "sales_staff"
  | "inventory_staff"
  | "viewer";

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  phone?: string;
  profile_image?: string | null;
  role: UserRole;
  status: string;
  is_active?: boolean;
};

export type AuthStatus = "bootstrapping" | "authenticated" | "anonymous";
