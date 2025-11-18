import React, { useState, useEffect } from "react";
import axios from "axios";
import MentorStats from "./MentorStats"; // Import the new component

// Helper function to format date (can be moved to a utils file)
const formatDate = (dateString) => {
  if (!dateString) return "Not Set";
  try {
    const date = new Date(dateString);
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return "Invalid Date";
    }
    return date.toLocaleDateString(undefined, {
      // Use locale default format
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch (e) {
    console.error("Error formatting date:", dateString, e);
    return "Invalid Date";
  }
};

// Helper function to construct Codeforces problem URL
const constructProblemUrl = (contestId, index) => {
  if (!contestId || !index || contestId === "Unknown") {
    return "#"; // Return a non-functional link or null if preferred
  }
  // Determine if it's a gym contest or regular contest
  const baseUrl =
    contestId.length > 4
      ? "https://codeforces.com/gym"
      : "https://codeforces.com/problemset/problem";
  return `${baseUrl}/${contestId}/${index}`;
};

// Helper to get today's date plus 7 days, formatted for input[type=date]
const getDefaultDueDate = () => {
  const date = new Date();
  date.setDate(date.getDate() + 7);
  return date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
};

const MentorDashboard = ({ user, API_URL }) => {
  const [learners, setLearners] = useState([]);
  const [learnersLoading, setLearnersLoading] = useState(true);
  const [learnersError, setLearnersError] = useState("");

  const [selectedLearner, setSelectedLearner] = useState(null); // Store the whole learner object
  const [selectedLearnerTasks, setSelectedLearnerTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState("");

  // State to manage the due dates being set for recommended tasks
  const [recommendedTaskDueDates, setRecommendedTaskDueDates] = useState({}); // { taskId: 'YYYY-MM-DD', ... }
  const [submittingTasks, setSubmittingTasks] = useState(false);

  // Modified to include 'stats' as a potential active tab
  const [activeTab, setActiveTab] = useState("profile"); // 'profile', 'tasks', or 'stats'
  
  // Add a refresh counter for the stats component
  const [statsRefreshTrigger, setStatsRefreshTrigger] = useState(0);

  // Fetch learners associated with this mentor
  useEffect(() => {
    const fetchLearners = async () => {
      if (!user || !user.id) return;
      setLearnersLoading(true);
      setLearnersError("");
      try {
        // Assuming the API uses the authenticated user's token to identify the mentor
        const response = await axios.get(
          `${API_URL}/mentor-relationships/mentor/${user.id}/learner-list`,
          {
            withCredentials: true,
          }
        );
        setLearners(response.data?.learners || []); // Extract the learners array from the response
      } catch (err) {
        console.error("Error fetching learners:", err);
        setLearnersError(
          `Failed to load learners. ${
            err.response?.data?.detail || err.message
          }`
        );
        setLearners([]); // Reset learners on error
      } finally {
        setLearnersLoading(false);
      }
    };

    fetchLearners();
  }, [user, API_URL]); // Depend on user and API_URL

  // Function to fetch learner tasks - extracted from useEffect
  const fetchLearnerTasks = async () => {
    if (!selectedLearner || !selectedLearner.id) return;

    setTasksLoading(true);
    setTasksError("");
    setSelectedLearnerTasks([]); // Clear previous tasks
    setRecommendedTaskDueDates({}); // Clear previous due dates

    try {
      const response = await axios.get(
        `${API_URL}/tasks/user/${selectedLearner.id}`,
        { withCredentials: true }
      );
      // Sort tasks: recommended first, then assigned, maybe by creation date?
      const sortedTasks = (response.data || []).sort((a, b) => {
        // Sort by hasbeensubmittedbymentor (false comes first), then maybe by title or id
        if (a.hasbeensubmittedbymentor !== b.hasbeensubmittedbymentor) {
          return a.hasbeensubmittedbymentor ? 1 : -1; // false first
        }
        return a.id - b.id; // Secondary sort
      });
      
      // Initialize due dates for all recommended tasks to default (today + 7 days)
      const defaultDueDate = getDefaultDueDate();
      const newDueDates = {};
      sortedTasks
        .filter(task => !task.hasbeensubmittedbymentor)
        .forEach(task => {
          newDueDates[task.id] = defaultDueDate;
        });
      
      setSelectedLearnerTasks(sortedTasks);
      setRecommendedTaskDueDates(newDueDates);
    } catch (err) {
      console.error("Error fetching learner tasks:", err);
      setTasksError(
        `Failed to load tasks for ${selectedLearner.name}. ${
          err.response?.data?.detail || err.message
        }`
      );
    } finally {
      setTasksLoading(false);
    }
  };

  // Update useEffect to use the extracted function
  useEffect(() => {
    fetchLearnerTasks();
  }, [selectedLearner, API_URL]); // Depend on selectedLearner

  // Handlers
  const handleLearnerSelect = (learner) => {
    setSelectedLearner(learner);
    setActiveTab("profile"); // Default to profile tab when selecting a new learner
  };

  // New handler for tab clicks with refresh functionality
  const handleTabClick = (tabName) => {
    setActiveTab(tabName);
    
    // Refresh data based on the selected tab
    if (tabName === "tasks" && selectedLearner) {
      fetchLearnerTasks();
    } else if (tabName === "stats") {
      // Trigger stats component refresh
      setStatsRefreshTrigger(prev => prev + 1);
    }
    // For "profile" tab, we don't typically need to refresh as the data is static
  };

  const handleDueDateChange = (taskId, date) => {
    setRecommendedTaskDueDates((prev) => ({
      ...prev,
      [taskId]: date,
    }));
  };

  const handleDeleteRecommendedTask = async (taskId) => {
    try {
      await axios.delete(`${API_URL}/tasks/${taskId}`);
      // Update UI after successful deletion
      setSelectedLearnerTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      setRecommendedTaskDueDates(prev => {
        const newState = { ...prev };
        delete newState[taskId];
        return newState;
      });
    } catch (err) {
      console.error("Error deleting task:", err);
      alert(`Failed to delete task: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleSubmitRecommendedTasks = async () => {
    const tasksToSubmit = selectedLearnerTasks
      .filter(
        (task) =>
          !task.hasbeensubmittedbymentor && recommendedTaskDueDates[task.id]
      )
      .map((task) => ({
        task_id: task.id,
        due_date: recommendedTaskDueDates[task.id],
      }));

    if (tasksToSubmit.length === 0) {
      alert(
        "Please set a due date for at least one recommended task before submitting."
      );
      return;
    }

    setSubmittingTasks(true);
    try {
      // Call the new API endpoint to assign tasks
      const response = await axios.post(
        `${API_URL}/tasks/assign`, 
        tasksToSubmit, 
        { withCredentials: true }
      );
      
      // Update state with the updated tasks from the response
      const updatedTasks = response.data;
      
      setSelectedLearnerTasks(prevTasks => {
        return prevTasks.map(task => {
          const updatedTask = updatedTasks.find(ut => ut.id === task.id);
          return updatedTask || task;
        });
      });
      
      // Clear due dates since they've been submitted
      setRecommendedTaskDueDates({});
      
      alert("Tasks assigned successfully!");
    } catch (err) {
      console.error("Error assigning tasks:", err);
      alert(`Failed to assign tasks: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSubmittingTasks(false);
    }
  };

  // Filter tasks for rendering
  const assignedTasks = selectedLearnerTasks.filter(
    (task) => task.hasbeensubmittedbymentor
  );
  const recommendedTasks = selectedLearnerTasks.filter(
    (task) => !task.hasbeensubmittedbymentor
  );

  // Render Logic
  if (learnersLoading) {
    return <div style={styles.loading}>Loading learners...</div>;
  }

  if (learnersError) {
    return <div style={styles.error}>{learnersError}</div>;
  }

  return (
    <div>
      {!selectedLearner ? (
        // View 1: Learner List
        <div style={styles.card}>
          <h2>Your Learners</h2>
          {learners.length === 0 ? (
            <p>You are not currently mentoring any learners.</p>
          ) : (
            <ul style={styles.learnerList}>
              {learners.map((learner) => (
                <li
                  key={learner.id}
                  style={styles.learnerItem}
                  onClick={() => handleLearnerSelect(learner)}
                >
                  <span>
                    {learner.name} ({learner.email})
                  </span>
                  <span style={styles.learnerArrow}>→</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        // View 2: Selected Learner Details
        <div>
          <button
            onClick={() => setSelectedLearner(null)}
            style={styles.backButton}
          >
            ← Back to Learner List
          </button>
          <h2 style={styles.learnerHeader}>Managing: {selectedLearner.name}</h2>

          {/* Tabs for Profile / Tasks / Stats - Updated to use handleTabClick */}
          <div style={styles.tabs}>
            <button
              style={
                activeTab === "profile"
                  ? { ...styles.tabButton, ...styles.activeTab }
                  : styles.tabButton
              }
              onClick={() => handleTabClick("profile")}
            >
              Profile
            </button>
            <button
              style={
                activeTab === "tasks"
                  ? { ...styles.tabButton, ...styles.activeTab }
                  : styles.tabButton
              }
              onClick={() => handleTabClick("tasks")}
            >
              Tasks
            </button>
            <button
              style={
                activeTab === "stats"
                  ? { ...styles.tabButton, ...styles.activeTab }
                  : styles.tabButton
              }
              onClick={() => handleTabClick("stats")}
            >
              Stats
            </button>
          </div>

          {/* Tab Content */}
          <div style={styles.card}>
            {activeTab === "profile" && (
              <div>
                <h3>Learner Profile</h3>
                <p>
                  <strong>Name:</strong> {selectedLearner.name}
                </p>
                <p>
                  <strong>Email:</strong> {selectedLearner.email}
                </p>
                {selectedLearner.codeforces_handle && (
                  <p>
                    <strong>Codeforces Handle:</strong>{" "}
                    <a 
                      href={`https://codeforces.com/profile/${selectedLearner.codeforces_handle}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={styles.profileLink}
                    >
                      {selectedLearner.codeforces_handle}
                    </a>
                  </p>
                )}
                <p>
                  <strong>Joined:</strong>{" "}
                  {formatDate(selectedLearner.date_created)}
                </p>
              </div>
            )}

            {activeTab === "tasks" && (
              <div>
                <h3>Tasks for {selectedLearner.name}</h3>
                {tasksLoading && (
                  <div style={styles.loading}>Loading tasks...</div>
                )}
                {tasksError && <div style={styles.error}>{tasksError}</div>}

                {!tasksLoading && !tasksError && (
                  <>
                    {/* Section 1: Recommended Tasks */}
                    <div style={styles.taskSection}>
                      <h4>Assign New Tasks</h4>
                      {recommendedTasks.length === 0 ? (
                        <p>No recommended tasks found for this learner.</p>
                      ) : (
                        <>
                          <table style={styles.taskTable}>
                            <thead>
                              <tr>
                                <th style={styles.tableHeader}>Problem</th>
                                <th style={styles.tableHeader}>Difficulty</th>
                                <th style={styles.tableHeader}>Set Due Date</th>
                                <th style={styles.tableHeader}>Actions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {recommendedTasks.map((task) => (
                                <tr key={task.id}>
                                  <td style={styles.tableCell}>
                                    <a
                                      href={constructProblemUrl(
                                        task.contestid,
                                        task.index
                                      )}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      title={`Contest ${task.contestid}, Index ${task.index}`}
                                      style={styles.taskLink}
                                    >
                                      {task.problem_name ||
                                        `Problem ${task.index}`}
                                    </a>
                                  </td>
                                  <td style={styles.tableCell}>{task.difficulty_category || "N/A"}</td>
                                  <td style={styles.tableCell}>
                                    <input
                                      type="date"
                                      value={
                                        recommendedTaskDueDates[task.id] || ""
                                      }
                                      onChange={(e) =>
                                        handleDueDateChange(
                                          task.id,
                                          e.target.value
                                        )
                                      }
                                      style={styles.dateInput}
                                      min={
                                        new Date().toISOString().split("T")[0]
                                      } // Prevent setting past dates
                                    />
                                  </td>
                                  <td style={styles.tableCell}>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation(); // Prevent row click
                                        handleDeleteRecommendedTask(task.id);
                                      }}
                                      style={styles.deleteButton}
                                    >
                                      Delete
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <button
                            onClick={handleSubmitRecommendedTasks}
                            style={styles.submitButton}
                            disabled={
                              Object.keys(recommendedTaskDueDates).length ===
                                0 || tasksLoading || submittingTasks
                            }
                          >
                            {submittingTasks ? "Assigning..." : "Assign Selected Tasks"}
                          </button>
                        </>
                      )}
                    </div>

                    {/* Section 2: Previously Assigned Tasks */}
                    <div style={styles.taskSection}>
                      <h4>Previously Assigned Tasks</h4>
                      {assignedTasks.length === 0 ? (
                        <p>No tasks have been assigned yet.</p>
                      ) : (
                        <table style={styles.taskTable}>
                          <thead>
                            <tr>
                              <th style={styles.tableHeader}>Problem</th>
                              <th style={styles.tableHeader}>Status</th>
                              <th style={styles.tableHeader}>Due Date</th>
                              <th style={styles.tableHeader}>Difficulty</th>
                            </tr>
                          </thead>
                          <tbody>
                            {assignedTasks.map((task) => (
                              <tr
                                key={task.id}
                                style={{
                                  ...styles.tableRow,
                                  ...(task.status === "overdue"
                                    ? styles.overdueRow
                                    : task.status === "completed"
                                    ? styles.completedRow
                                    : {})
                                }}
                              >
                                <td style={styles.tableCell}>
                                  <a
                                    href={constructProblemUrl(
                                      task.contestid,
                                      task.index
                                    )}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    title={`Contest ${task.contestid}, Index ${task.index}`}
                                    style={styles.taskLink}
                                  >
                                    {task.problem_name ||
                                      `Problem ${task.index}`}
                                  </a>
                                </td>
                                <td style={styles.tableCell}>
                                  <span
                                    style={{
                                      ...styles.statusBadge,
                                      ...styles.statusColors[
                                        task.status || "pending"
                                      ],
                                    }}
                                  >
                                    {task.status}
                                  </span>
                                </td>
                                <td style={styles.tableCell}>{formatDate(task.due_date)}</td>
                                <td style={styles.tableCell}>{task.difficulty_category || "N/A"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Updated Stats Tab Content with refreshTrigger */}
            {activeTab === "stats" && (
              <div>
                {!selectedLearner.codeforces_handle ? (
                  <div style={styles.noCodeforcesHandle}>
                    <h3>No Codeforces Handle Available</h3>
                    <p>This learner hasn't linked their Codeforces account yet. Please ask them to update their profile.</p>
                  </div>
                ) : (
                  <MentorStats 
                    learner={selectedLearner} 
                    API_URL={API_URL} 
                    refreshTrigger={statsRefreshTrigger}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Styles - Original styles plus new additions
const styles = {
  loading: {
    padding: "20px",
    textAlign: "center",
    color: "#555",
  },
  error: {
    backgroundColor: "#ffebee",
    color: "#c62828",
    padding: "15px",
    borderRadius: "4px",
    margin: "10px 0",
    border: "1px solid #e57373",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    padding: "25px",
    boxShadow: "0 3px 10px rgba(0, 0, 0, 0.08)",
    marginTop: "20px",
  },
  learnerList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  },
  learnerItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "15px 10px",
    borderBottom: "1px solid #eee",
    cursor: "pointer",
    transition: "background-color 0.2s",
    "&:hover": {
      backgroundColor: "#f5f5f5",
    },
  },
  learnerArrow: {
    color: "#2196f3",
    fontSize: "18px",
  },
  backButton: {
    backgroundColor: "transparent",
    border: "none",
    color: "#2196f3",
    cursor: "pointer",
    fontSize: "16px",
    padding: "5px 0",
    display: "flex",
    alignItems: "center",
    marginBottom: "10px",
  },
  learnerHeader: {
    margin: "10px 0 20px",
    color: "#333",
  },
  tabs: {
    display: "flex",
    marginBottom: "0px",
    borderBottom: "1px solid #e0e0e0",
  },
  tabButton: {
    backgroundColor: "transparent",
    border: "none",
    borderBottom: "3px solid transparent",
    padding: "12px 20px",
    cursor: "pointer",
    fontSize: "16px",
    color: "#555",
    marginRight: "5px",
  },
  activeTab: {
    borderBottom: "3px solid #2196f3",
    color: "#2196f3",
    fontWeight: "500",
  },
  taskSection: {
    marginBottom: "30px",
  },
  taskTable: {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: "15px",
  },
  tableHeader: {
    textAlign: "left",
    padding: "12px 15px",
    backgroundColor: "#f5f5f5",
    borderBottom: "1px solid #ddd",
  },
  tableCell: {
    padding: "12px 15px",
    borderBottom: "1px solid #eee",
  },
  tableRow: {
    transition: "background-color 0.2s",
  },
  overdueRow: {
    backgroundColor: "#fff8e1",
  },
  completedRow: {
    backgroundColor: "#f1f8e9",
  },
  taskLink: {
    color: "#1976d2",
    textDecoration: "none",
    "&:hover": {
      textDecoration: "underline",
    },
  },
  statusBadge: {
    padding: "5px 8px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "500",
    display: "inline-block",
  },
  statusColors: {
    completed: {
      backgroundColor: "#e8f5e9",
      color: "#2e7d32",
    },
    pending: {
      backgroundColor: "#e3f2fd",
      color: "#1565c0",
    },
    overdue: {
      backgroundColor: "#ffebee",
      color: "#c62828",
    },
    "in progress": {
      backgroundColor: "#ede7f6",
      color: "#4527a0",
    },
  },
  dateInput: {
    padding: "8px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    width: "100%",
  },
  submitButton: {
    backgroundColor: "#2196f3",
    color: "white",
    border: "none",
    padding: "10px 15px",
    borderRadius: "4px",
    cursor: "pointer",
    marginTop: "15px",
    "&:disabled": {
      backgroundColor: "#bdbdbd",
      cursor: "not-allowed",
    },
  },
  deleteButton: {
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    padding: "5px 10px",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "12px",
  },
  profileLink: {
    color: "#1976d2",
    textDecoration: "none",
    "&:hover": {
      textDecoration: "underline",
    },
  },
  noCodeforcesHandle: {
    textAlign: "center",
    padding: "30px 15px",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
  }
};

export default MentorDashboard;