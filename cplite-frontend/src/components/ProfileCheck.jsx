import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProfileCheck = () => {
  const { user } = useAuth();

  console.log('ProfileCheck executed:', { user });

  if (!user?.codeforces_handle) {
    console.log('No codeforces_handle, redirecting to profile-setup');
    return <Navigate to="/profile-setup" replace />;
  }

  return <Outlet />;
};

export default ProfileCheck;