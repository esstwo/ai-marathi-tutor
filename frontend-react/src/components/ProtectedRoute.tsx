import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireChild?: boolean;
}

const ProtectedRoute = ({ children, requireChild = true }: ProtectedRouteProps) => {
  const { isAuthenticated, activeChild } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireChild && !activeChild) {
    return <Navigate to="/child-setup" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
