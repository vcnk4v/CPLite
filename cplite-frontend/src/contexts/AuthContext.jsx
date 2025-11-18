import { createContext, useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { jwtDecode } from "jwt-decode";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Check if token is expired
  const isTokenExpired = (token) => {
    try {
      const decoded = jwtDecode(token);
      return decoded.exp * 1000 < Date.now();
    } catch (error) {
      return true;
    }
  };

  // Set axios auth header
  const setAuthHeader = (token) => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common["Authorization"];
    }
  };

  // Refresh the access token
  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem("refreshToken");
      if (!refreshToken) {
        throw new Error("No refresh token");
      }

      const response = await axios.post(`${API_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token } = response.data;
      localStorage.setItem("accessToken", access_token);
      localStorage.setItem("refreshToken", refresh_token);
      setAuthHeader(access_token);

      return access_token;
    } catch (error) {
      console.error("Failed to refresh token:", error);
      logout();
      return null;
    }
  };

  // Setup axios interceptor for token refresh
  useEffect(() => {
    const setupInterceptors = () => {
      axios.interceptors.request.use(
        async (config) => {
          const accessToken = localStorage.getItem("accessToken");

          if (accessToken && isTokenExpired(accessToken)) {
            const newToken = await refreshToken();
            if (newToken) {
              config.headers.Authorization = `Bearer ${newToken}`;
            }
          } else if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
          }

          return config;
        },
        (error) => Promise.reject(error)
      );

      axios.interceptors.response.use(
        (response) => response,
        async (error) => {
          const originalRequest = error.config;

          if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const token = await refreshToken();

            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return axios(originalRequest);
            }
          }

          return Promise.reject(error);
        }
      );
    };

    setupInterceptors();
  }, []);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      const accessToken = localStorage.getItem("accessToken");

      if (accessToken) {
        if (isTokenExpired(accessToken)) {
          try {
            await refreshToken();
            fetchUserProfile();
          } catch (error) {
            setUser(null);
            setLoading(false);
          }
        } else {
          setAuthHeader(accessToken);
          fetchUserProfile();
        }
      } else {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // Fetch user profile
  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API_URL}/users/me`);
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Login with Google
  const loginWithGoogle = async (googleToken) => {
    try {
      console.log("Sending Google token to backend:", googleToken);

      const response = await axios.post(`${API_URL}/auth/google`, {
        token: googleToken,
      });

      const { access_token, refresh_token } = response.data;

      localStorage.setItem("accessToken", access_token);
      localStorage.setItem("refreshToken", refresh_token);
      setAuthHeader(access_token);

      await fetchUserProfile();
      return { success: true };
    } catch (error) {
      console.error("Google login failed:", error);
      return {
        success: false,
        message: error.response?.data?.detail || "Google login failed",
      };
    }
  };

  // Logout
  const logout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    setAuthHeader(null);
    setUser(null);
    navigate("/login");
  };

  const authContextValue = {
    user,
    loading,
    loginWithGoogle,
    logout,
    refreshToken,
    isAuthenticated: !!user,
    fetchUserProfile,
  };

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};
