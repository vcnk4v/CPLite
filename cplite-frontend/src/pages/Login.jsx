// import { useEffect, useRef } from 'react';
// import { useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';

// const Login = () => {
//   const googleButtonRef = useRef(null);
//   const { loginWithGoogle, isAuthenticated, loading } = useAuth();
//   const navigate = useNavigate();

//   useEffect(() => {
//     if (isAuthenticated) {
//       navigate('/dashboard');
//     }
//   }, [isAuthenticated, navigate]);

//   useEffect(() => {
//     // Load the Google Identity Services script
//     const loadGoogleScript = () => {
//       const script = document.createElement('script');
//       script.src = 'https://accounts.google.com/gsi/client';
//       script.async = true;
//       script.defer = true;
//       document.body.appendChild(script);

//       script.onload = initializeGoogleButton;
//       return () => {
//         document.body.removeChild(script);
//       };
//     };

//     // Initialize Google Sign-In button once the script is loaded
//     const initializeGoogleButton = () => {
//       if (window.google && googleButtonRef.current) {
//         window.google.accounts.id.initialize({
//           client_id: '967529061111-bakbh7amrv9vmu7bg9gaisf0ca251u2s.apps.googleusercontent.com', // Use your Google client ID
//           callback: handleGoogleResponse,
//           auto_select: false,
//         });

//         window.google.accounts.id.renderButton(googleButtonRef.current, {
//           theme: 'outline',
//           size: 'large',
//           width: 320,
//           text: 'signin_with',
//         });
//       }
//     };

//     return loadGoogleScript();
//   }, []);

//   // Handle Google Sign-In response
//   const handleGoogleResponse = async (response) => {
//     console.log('Google response:', response);

//     if (response.credential) {
//       // Send the ID token to your backend
//       const result = await loginWithGoogle(response.credential);

//       if (result.success) {
//         navigate('/dashboard');
//       } else {
//         console.error('Google login failed:', result.message);
//         alert(`Login failed: ${result.message}`);
//       }
//     }
//   };

//   if (loading) {
//     return <div style={styles.loading}>Loading...</div>;
//   }

//   return (
//     <div style={styles.container}>
//       <div style={styles.loginBox}>
//         <h1 style={styles.title}>CPLite</h1>
//         <p style={styles.subtitle}>A Personalized E-Learning Platform for Competitive Programming</p>

//         <div style={styles.googleLoginContainer}>
//           <p style={styles.loginText}>Sign in with Google to continue:</p>
//           <div ref={googleButtonRef} style={styles.googleButton}></div>
//         </div>
//       </div>
//     </div>
//   );
// };

// // Simple inline styles
// const styles = {
//   container: {
//     display: 'flex',
//     justifyContent: 'center',
//     alignItems: 'center',
//     height: '100vh',
//     backgroundColor: '#f5f5f5',
//   },
//   loginBox: {
//     backgroundColor: '#fff',
//     padding: '40px',
//     borderRadius: '8px',
//     boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
//     textAlign: 'center',
//     maxWidth: '400px',
//     width: '100%',
//   },
//   title: {
//     margin: '0 0 10px 0',
//     color: '#333',
//   },
//   subtitle: {
//     margin: '0 0 30px 0',
//     color: '#666',
//     fontSize: '14px',
//   },
//   googleLoginContainer: {
//     display: 'flex',
//     flexDirection: 'column',
//     alignItems: 'center',
//     marginTop: '20px',
//   },
//   loginText: {
//     marginBottom: '15px',
//     color: '#555',
//   },
//   googleButton: {
//     width: '100%',
//   },
//   loading: {
//     display: 'flex',
//     justifyContent: 'center',
//     alignItems: 'center',
//     height: '100vh',
//   }
// };

// export default Login;

import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const Login = () => {
  const googleButtonRef = useRef(null);
  const { loginWithGoogle, isAuthenticated, loading, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      // Check if user has a Codeforces handle linked
      if (user && user.codeforces_handle) {
        navigate("/dashboard");
      } else {
        navigate("/profile-setup");
      }
    }
  }, [isAuthenticated, navigate, user]);

  useEffect(() => {
    // Load the Google Identity Services script
    const loadGoogleScript = () => {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      document.body.appendChild(script);

      script.onload = initializeGoogleButton;
      return () => {
        document.body.removeChild(script);
      };
    };

    // Initialize Google Sign-In button once the script is loaded
    const initializeGoogleButton = () => {
      if (window.google && googleButtonRef.current) {
        window.google.accounts.id.initialize({
          client_id:
            "967529061111-bakbh7amrv9vmu7bg9gaisf0ca251u2s.apps.googleusercontent.com", // Use your Google client ID
          callback: handleGoogleResponse,
          auto_select: false,
        });

        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
          text: "signin_with",
        });
      }
    };

    return loadGoogleScript();
  }, []);

  // Handle Google Sign-In response
  const handleGoogleResponse = async (response) => {
    console.log("Google response:", response);

    if (response.credential) {
      // Send the ID token to your backend
      const result = await loginWithGoogle(response.credential);

      if (result.success) {
        // Navigation will be handled by the useEffect above
      } else {
        console.error("Google login failed:", result.message);
        alert(`Login failed: ${result.message}`);
      }
    }
  };

  if (loading) {
    return <div style={styles.loading}>Loading...</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.loginBox}>
        <h1 style={styles.title}>CPLite</h1>
        <p style={styles.subtitle}>
          A Personalized E-Learning Platform for Competitive Programming
        </p>

        <div style={styles.googleLoginContainer}>
          <p style={styles.loginText}>Sign in with Google to continue:</p>
          <div ref={googleButtonRef} style={styles.googleButton}></div>
        </div>
      </div>
    </div>
  );
};

// Simple inline styles
const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundColor: "#f5f5f5",
  },
  loginBox: {
    backgroundColor: "#fff",
    padding: "40px",
    borderRadius: "8px",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
    textAlign: "center",
    maxWidth: "400px",
    width: "100%",
  },
  title: {
    margin: "0 0 10px 0",
    color: "#333",
  },
  subtitle: {
    margin: "0 0 30px 0",
    color: "#666",
    fontSize: "14px",
  },
  googleLoginContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    marginTop: "20px",
  },
  loginText: {
    marginBottom: "15px",
    color: "#555",
  },
  googleButton: {
    width: "100%",
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
  },
};

export default Login;
