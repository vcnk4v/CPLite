import { useState, useEffect } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const ProfileSetup = () => {
  const { user, fetchUserProfile, refreshToken } = useAuth();
  const navigate = useNavigate();

  // Setup steps
  const STEPS = {
    ROLE_SELECTION: 1,
    PROFILE_DETAILS: 2,
  };

  const [currentStep, setCurrentStep] = useState(STEPS.ROLE_SELECTION);
  const [selectedRole, setSelectedRole] = useState("");
  const [codeforcesHandle, setCodeforcesHandle] = useState("");
  const [mentors, setMentors] = useState([]);
  const [selectedMentor, setSelectedMentor] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    console.log("ProfileSetup component mounted");
    console.log("Current user:", user?.name);
  }, []);

  useEffect(() => {
    if (user?.codeforces_handle) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    const fetchMentors = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `${API_URL}/mentor-relationships/mentors/available`
        );
        setMentors(response.data);
        setError("");
      } catch (err) {
        setError("Failed to load mentors. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    // Only fetch mentors if we're on the profile details step and user is a learner
    if (
      user &&
      !user.codeforces_handle &&
      currentStep === STEPS.PROFILE_DETAILS &&
      selectedRole === "learner"
    ) {
      fetchMentors();
    } else if (
      currentStep === STEPS.ROLE_SELECTION ||
      selectedRole === "mentor"
    ) {
      setLoading(false);
    }
  }, [user, currentStep, selectedRole]);

  const handleRoleSelection = (role) => {
    setSelectedRole(role);
    setCurrentStep(STEPS.PROFILE_DETAILS);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!codeforcesHandle.trim()) {
      setError("Please enter your Codeforces handle");
      return;
    }

    if (selectedRole === "learner" && !selectedMentor) {
      setError("Please select a mentor");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      // First update user role
      await axios.put(`${API_URL}/users/me/role`, {
        role: selectedRole,
      });

      await refreshToken();

      // Then update profile with Codeforces handle
      await axios.put(`${API_URL}/users/me`, {
        codeforces_handle: codeforcesHandle,
      });

      // For learners, also create the mentor-learner relationship
      if (selectedRole === "learner") {
        await axios.post(`${API_URL}/mentor-relationships/assign-mentor`, {
          learner_id: user.id,
          mentor_id: parseInt(selectedMentor),
        });
      }

      await fetchUserProfile();
      setSuccess("Profile setup successful! Redirecting...");

      setTimeout(() => {
        navigate("/dashboard", { replace: true });
      }, 2000);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Profile setup failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (
    loading &&
    currentStep === STEPS.PROFILE_DETAILS &&
    selectedRole === "learner"
  ) {
    return <div style={styles.loading}>Loading mentors...</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.formBox}>
        <h1 style={styles.title}>Complete Your Profile</h1>

        {/* Progress indicators */}
        <div style={styles.stepIndicator}>
          <div
            style={{
              ...styles.stepDot,
              ...(currentStep === STEPS.ROLE_SELECTION
                ? styles.activeStep
                : {}),
            }}
          >
            1
          </div>
          <div style={styles.stepLine}></div>
          <div
            style={{
              ...styles.stepDot,
              ...(currentStep === STEPS.PROFILE_DETAILS
                ? styles.activeStep
                : {}),
            }}
          >
            2
          </div>
        </div>

        <p style={styles.subtitle}>
          {currentStep === STEPS.ROLE_SELECTION
            ? "Choose your role in the platform"
            : selectedRole === "learner"
            ? "Link your Codeforces account and select a mentor"
            : "Link your Codeforces account to continue"}
        </p>

        {error && <div style={styles.errorMessage}>{error}</div>}
        {success && <div style={styles.successMessage}>{success}</div>}

        {currentStep === STEPS.ROLE_SELECTION ? (
          <div style={styles.roleSelection}>
            <button
              style={{
                ...styles.roleButton,
                ...(selectedRole === "learner" ? styles.selectedRole : {}),
              }}
              onClick={() => handleRoleSelection("learner")}
            >
              I want to be a Learner
              <p style={styles.roleDescription}>
                Get matched with a mentor and start learning
              </p>
            </button>
            <button
              style={{
                ...styles.roleButton,
                ...(selectedRole === "mentor" ? styles.selectedRole : {}),
              }}
              onClick={() => handleRoleSelection("mentor")}
            >
              I want to be a Mentor
              <p style={styles.roleDescription}>
                Help others improve their skills
              </p>
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.formGroup}>
              <label htmlFor="codeforcesHandle" style={styles.label}>
                Codeforces Handle
              </label>
              <input
                id="codeforcesHandle"
                type="text"
                value={codeforcesHandle}
                onChange={(e) => setCodeforcesHandle(e.target.value)}
                placeholder="Enter your Codeforces handle"
                style={styles.input}
                required
              />
            </div>

            {selectedRole === "learner" && (
              <div style={styles.formGroup}>
                <label htmlFor="mentor" style={styles.label}>
                  Select a Mentor
                </label>
                <select
                  id="mentor"
                  value={selectedMentor}
                  onChange={(e) => setSelectedMentor(e.target.value)}
                  style={styles.input}
                  required
                  disabled={submitting}
                >
                  <option value="">-- Select a mentor --</option>
                  {mentors.map((mentor) => (
                    <option key={mentor.id} value={mentor.id}>
                      {mentor.name} ({mentor.codeforces_handle || ""}) -{" "}
                      {mentor.url || ""}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {selectedRole === "learner" && selectedMentor && (
              <div style={styles.selectedMentor}>
                <p style={styles.mentorTitle}>Selected Mentor:</p>
                <p>
                  <strong>
                    {
                      mentors.find((m) => m.id === parseInt(selectedMentor))
                        ?.name
                    }
                  </strong>
                  <a
                    href={`https://codeforces.com/profile/${
                      mentors.find((m) => m.id === parseInt(selectedMentor))
                        ?.codeforces_handle
                    }`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.mentorLink}
                  >
                    View Codeforces Profile
                  </a>
                </p>
              </div>
            )}

            <div style={styles.buttonGroup}>
              <button
                type="button"
                onClick={() => setCurrentStep(STEPS.ROLE_SELECTION)}
                style={styles.backButton}
                disabled={submitting || !!success}
              >
                Back
              </button>
              <button
                type="submit"
                style={styles.submitButton}
                disabled={submitting || !!success}
              >
                {submitting ? "Setting up..." : "Complete Setup"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

// Updated styles
const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    backgroundColor: "#f5f5f5",
    padding: "20px",
  },
  formBox: {
    backgroundColor: "#fff",
    padding: "40px",
    borderRadius: "8px",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
    width: "100%",
    maxWidth: "500px",
  },
  title: {
    margin: "0 0 20px 0",
    color: "#333",
    textAlign: "center",
  },
  subtitle: {
    margin: "0 0 30px 0",
    color: "#666",
    fontSize: "14px",
    textAlign: "center",
  },
  stepIndicator: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    margin: "0 0 30px 0",
  },
  stepDot: {
    width: "30px",
    height: "30px",
    borderRadius: "50%",
    backgroundColor: "#ddd",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    color: "#666",
    fontWeight: "bold",
  },
  activeStep: {
    backgroundColor: "#4285F4",
    color: "#fff",
  },
  stepLine: {
    height: "2px",
    width: "50px",
    backgroundColor: "#ddd",
    margin: "0 10px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  formGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "14px",
    fontWeight: "bold",
    color: "#444",
  },
  input: {
    padding: "12px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "16px",
    width: "100%",
  },
  roleSelection: {
    display: "flex",
    flexDirection: "column",
    gap: "15px",
  },
  roleButton: {
    padding: "20px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    backgroundColor: "#fff",
    textAlign: "left",
    cursor: "pointer",
    transition: "all 0.3s",
    fontSize: "16px",
    fontWeight: "bold",
  },
  selectedRole: {
    borderColor: "#4285F4",
    backgroundColor: "#F0F8FF",
    boxShadow: "0 2px 4px rgba(66, 133, 244, 0.2)",
  },
  roleDescription: {
    margin: "5px 0 0",
    fontWeight: "normal",
    fontSize: "14px",
    color: "#666",
  },
  buttonGroup: {
    display: "flex",
    justifyContent: "space-between",
    gap: "10px",
    marginTop: "10px",
  },
  backButton: {
    flex: "1",
    backgroundColor: "#f5f5f5",
    color: "#444",
    border: "1px solid #ddd",
    borderRadius: "4px",
    padding: "12px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    transition: "background-color 0.3s",
  },
  submitButton: {
    flex: "2",
    backgroundColor: "#4285F4",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    padding: "12px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
    transition: "background-color 0.3s",
  },
  errorMessage: {
    backgroundColor: "#FFEBEE",
    color: "#D32F2F",
    padding: "12px",
    borderRadius: "4px",
    marginBottom: "20px",
    fontSize: "14px",
    textAlign: "center",
  },
  successMessage: {
    backgroundColor: "#E8F5E9",
    color: "#2E7D32",
    padding: "12px",
    borderRadius: "4px",
    marginBottom: "20px",
    fontSize: "14px",
    textAlign: "center",
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
  },
  selectedMentor: {
    backgroundColor: "#F0F8FF",
    padding: "15px",
    borderRadius: "4px",
    marginBottom: "10px",
  },
  mentorTitle: {
    fontWeight: "bold",
    marginBottom: "5px",
    fontSize: "14px",
  },
  mentorLink: {
    color: "#4285F4",
    textDecoration: "none",
    fontSize: "14px",
    marginLeft: "10px",
  },
};

export default ProfileSetup;
