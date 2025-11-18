import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const ProtectedRoute = () => {
  const { isAuthenticated, loading, user } = useAuth();

  console.log("ProtectedRoute executed:", { isAuthenticated, loading, user });

  if (loading) {
    console.log("Auth loading...");
    return <div>Loading authentication...</div>;
  }

  if (!isAuthenticated) {
    console.log("Not authenticated, redirecting to login");
    return <Navigate to="/login" replace />;
  }

  console.log("Authentication passed, rendering outlet");
  return <Outlet />;
};

export default ProtectedRoute;
