import React, { useState, useEffect } from "react";
import axios from "axios";
import LearnerStats from "./LearnerStats"; // Import the LearnerStats component

const LearnerDashboard = ({ user, API_URL, logout }) => {
  // State for tabs - add "statistics" to possible tab values
  const [activeTab, setActiveTab] = useState("profile");

  // Tasks state
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState("");

  // Notifications state
  const [notifications, setNotifications] = useState([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState("");

  // Task dialog state
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [taskStatusUpdating, setTaskStatusUpdating] = useState(false);

  // Fetch data based on active tab when user or activeTab changes
  useEffect(() => {
    if (!user) return; // Don't fetch if user is not loaded

    if (activeTab === "tasks") {
      fetchTasks();
    } else if (activeTab === "notifications") {
      fetchNotifications();
    }
    // No fetch needed for 'profile' or 'statistics' as they handle their own data
  }, [user, activeTab, API_URL]);

  const fetchTasks = async () => {
    if (!user) return;
    setTasksLoading(true);
    setTasksError("");
    try {
      const response = await axios.get(`${API_URL}/tasks/user/${user.id}`);
      setTasks(response.data);
    } catch (err) {
      console.error("Error fetching tasks:", err);
      setTasksError(
        "Failed to load tasks. Check service availability and authentication."
      );
    } finally {
      setTasksLoading(false);
    }
  };

  const fetchNotifications = async () => {
    if (!user) return;
    setNotificationsLoading(true);
    setNotificationsError("");
    try {
      // First publish contest notifications
      await publishContestNotifications();

      // Then fetch user notifications
      const response = await axios.get(
        `${API_URL}/notification/user/${user.id}`
      );
      // Sort notifications by creation date, newest first
      const sortedNotifications = response.data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setNotifications(sortedNotifications);
    } catch (err) {
      console.error("Error fetching notifications:", err);
      setNotificationsError(
        "Failed to load notifications. Check service availability and authentication."
      );
    } finally {
      setNotificationsLoading(false);
    }
  };

  // New function to publish contest notifications
  const publishContestNotifications = async () => {
    try {
      await axios.post(`${API_URL}/codeforces/contests/publish-notifications`);
      console.log("Contest notifications published successfully");
    } catch (err) {
      console.error("Error publishing contest notifications:", err);
      // We don't want to break the notification fetching if this fails
      // So we just log the error but don't throw
    }
  };

  const updateTaskStatus = async (taskId, newStatus) => {
    setTaskStatusUpdating(true);
    try {
      await axios.put(`${API_URL}/tasks/${taskId}`, { status: newStatus });
      
      // Update local tasks state
      setTasks(
        tasks.map((task) =>
          task.id === taskId ? { ...task, status: newStatus } : task
        )
      );
      
      // If we're in the dialog, update the selected task too
      if (selectedTask && selectedTask.id === taskId) {
        setSelectedTask({...selectedTask, status: newStatus});
      }
      
      return true;
    } catch (err) {
      console.error("Error updating task:", err);
      alert("Failed to update task status");
      return false;
    } finally {
      setTaskStatusUpdating(false);
    }
  };

  const openTaskDialog = (task) => {
    setSelectedTask(task);
    setShowTaskDialog(true);
  };

  const closeTaskDialog = () => {
    setShowTaskDialog(false);
    setSelectedTask(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getTaskStatusBadge = (taskStatus) => {
    switch(taskStatus) {
      case 'completed':
        return <span style={styles.statusBadgeCompleted}>Completed</span>;
      case 'overdue':
        return <span style={styles.statusBadgeOverdue}>Overdue</span>;
      default:
        return <span style={styles.statusBadgePending}>Pending</span>;
    }
  };

  // Construct Codeforces problem URL
  const getProblemUrl = (contestId, index) => {
    if (!contestId || !index || contestId === "Unknown") {
      return "#";
    }
    // Determine if it's a gym contest or regular contest
    const baseUrl =
      contestId.length > 4
        ? "https://codeforces.com/gym"
        : "https://codeforces.com/problemset/problem";
    return `${baseUrl}/${contestId}/${index}`;
  };

  if (!user) {
    return <div>Loading user data...</div>;
  }

  return (
    <div style={styles.container}>
      {/* Task Dialog */}
      {showTaskDialog && selectedTask && (
        <div style={styles.dialogOverlay}>
          <div style={styles.dialogContent}>
            <button style={styles.closeButton} onClick={closeTaskDialog}>×</button>
            <h2 style={styles.dialogTitle}>{selectedTask.problem_name}</h2>
            
            <div style={styles.dialogInfo}>
              <div style={styles.dialogInfoRow}>
                <span style={styles.dialogLabel}>Status:</span>
                {getTaskStatusBadge(selectedTask.status)}
              </div>
              
              <div style={styles.dialogInfoRow}>
                <span style={styles.dialogLabel}>Due Date:</span>
                <span>{formatDate(selectedTask.due_date)}</span>
              </div>
              
              {selectedTask.difficulty && (
                <div style={styles.dialogInfoRow}>
                  <span style={styles.dialogLabel}>Difficulty:</span>
                  <span>{selectedTask.difficulty} ({selectedTask.difficulty_category || 'Unknown'})</span>
                </div>
              )}
              
              {selectedTask.tags && selectedTask.tags.length > 0 && (
                <div style={styles.dialogInfoRow}>
                  <span style={styles.dialogLabel}>Tags:</span>
                  <div style={styles.tagContainer}>
                    {selectedTask.tags.map((tag, index) => (
                      <span key={index} style={styles.tag}>{tag}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div style={styles.dialogActions}>
              <a 
                href={getProblemUrl(selectedTask.contestid, selectedTask.index)}
                target="_blank" 
                rel="noopener noreferrer"
                style={styles.dialogOpenButton}
              >
                Open Problem on Codeforces
              </a>
              
              {selectedTask.status !== 'completed' ? (
                <button 
                  onClick={() => updateTaskStatus(selectedTask.id, 'completed')} 
                  style={styles.dialogCompleteButton}
                  disabled={taskStatusUpdating}
                >
                  {taskStatusUpdating ? 'Updating...' : 'Mark as Completed'}
                </button>
              ) : (
                <button 
                  onClick={() => updateTaskStatus(selectedTask.id, 'pending')} 
                  style={styles.dialogResetButton}
                  disabled={taskStatusUpdating}
                >
                  {taskStatusUpdating ? 'Updating...' : 'Mark as Pending'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <div style={styles.header}>
        <h1>Learner Dashboard</h1>
        {logout && (
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        )}
      </div>

      {/* Tabs Navigation - Add Statistics tab */}
      <div style={styles.tabs}>
        <button
          style={
            activeTab === "profile"
              ? { ...styles.tabButton, ...styles.activeTab }
              : styles.tabButton
          }
          onClick={() => setActiveTab("profile")}
        >
          Profile
        </button>
        <button
          style={
            activeTab === "tasks"
              ? { ...styles.tabButton, ...styles.activeTab }
              : styles.tabButton
          }
          onClick={() => setActiveTab("tasks")}
        >
          Tasks
        </button>
        <button
          style={
            activeTab === "statistics"
              ? { ...styles.tabButton, ...styles.activeTab }
              : styles.tabButton
          }
          onClick={() => setActiveTab("statistics")}
        >
          Statistics
        </button>
        <button
          style={
            activeTab === "notifications"
              ? { ...styles.tabButton, ...styles.activeTab }
              : styles.tabButton
          }
          onClick={() => setActiveTab("notifications")}
        >
          Notifications
        </button>
      </div>

      {/* Profile Tab Content */}
      {activeTab === "profile" && (
        <div style={styles.card}>
          <h2>Your Profile</h2>
          <div style={styles.userInfo}>
            <p>
              <strong>Name:</strong> {user.name}
            </p>
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            {user.codeforces_handle && (
              <p>
                <strong>Codeforces Handle:</strong>{" "}
                <a 
                  href={`https://codeforces.com/profile/${user.codeforces_handle}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={styles.codeforcesLink}
                >
                  {user.codeforces_handle}
                </a>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tasks Tab Content */}
      {activeTab === "tasks" && (
        <div style={styles.card}>
          <div style={styles.taskHeader}>
            <h2>Your Tasks</h2>
            <button
              onClick={fetchTasks}
              style={styles.refreshButton}
              disabled={tasksLoading}
            >
              {tasksLoading ? "Refreshing..." : "Refresh Tasks"}
            </button>
          </div>

          {tasksLoading && <p style={styles.loadingText}>Loading tasks...</p>}

          {tasksError && (
            <div style={styles.error}>
              <p>{tasksError}</p>
            </div>
          )}

          {!tasksLoading && !tasksError && tasks.length === 0 && (
            <p style={styles.emptyMessage}>
              You don't have any assigned tasks yet. 
              Your mentor will assign programming problems for you to solve.
            </p>
          )}

          {!tasksLoading && !tasksError && tasks.length > 0 && (
            <div style={styles.taskGrid}>
              {tasks.map((task) => (
                <div 
                  key={task.id} 
                  style={{
                    ...styles.taskCard,
                    ...(task.status === 'completed' ? styles.taskCardCompleted : 
                        task.status === 'overdue' ? styles.taskCardOverdue : {})
                  }}
                  onClick={() => openTaskDialog(task)}
                >
                  <h3 style={styles.taskTitle}>{task.problem_name}</h3>
                  
                  <div style={styles.taskMeta}>
                    <div>
                      {getTaskStatusBadge(task.status)}
                    </div>
                    <div style={styles.taskDueDate}>
                      Due: {formatDate(task.due_date)}
                    </div>
                  </div>
                  
                  {task.difficulty_category && (
                    <div style={styles.taskDifficulty}>
                      {task.difficulty_category}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Statistics Tab Content - New tab */}
      {activeTab === "statistics" && (
        <div style={styles.card}>
          <LearnerStats 
            user={{ handle: user.codeforces_handle }} 
            API_URL={API_URL} 
          />
        </div>
      )}

      {/* Notifications Tab Content */}
      {activeTab === "notifications" && (
        <div style={styles.card}>
          <div style={styles.notificationHeader}>
            <h2>Notifications</h2>
            <button
              onClick={fetchNotifications}
              style={styles.refreshButton}
              disabled={notificationsLoading}
            >
              {notificationsLoading ? "Refreshing..." : "Refresh Notifications"}
            </button>
          </div>

          {notificationsLoading && <p>Loading notifications...</p>}

          {notificationsError && (
            <div style={styles.error}>
              <p>{notificationsError}</p>
            </div>
          )}

          {!notificationsLoading &&
            !notificationsError &&
            notifications.length === 0 && <p>You have no notifications.</p>}

          {!notificationsLoading &&
            !notificationsError &&
            notifications.length > 0 && (
              <div style={styles.notificationList}>
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    style={{
                      ...styles.notificationItem,
                      ...(notification.is_read
                        ? styles.notificationRead
                        : styles.notificationUnread),
                    }}
                  >
                    <p style={styles.notificationContent}>
                      {notification.content}
                    </p>
                    <div style={styles.notificationMeta}>
                      <span style={styles.notificationDate}>
                        {formatDate(notification.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    padding: "25px",
    boxShadow: "0 3px 10px rgba(0, 0, 0, 0.08)",
    marginTop: "20px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },
  logoutButton: {
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    padding: "8px 16px",
    borderRadius: "4px",
    cursor: "pointer",
  },
  tabs: {
    display: "flex",
    borderBottom: "1px solid #ddd",
    marginBottom: "20px",
  },
  tabButton: {
    padding: "10px 20px",
    border: "none",
    backgroundColor: "transparent",
    cursor: "pointer",
    fontSize: "16px",
  },
  activeTab: {
    borderBottom: "3px solid #4285f4",
    color: "#4285f4",
    fontWeight: "bold",
  },
  card: {
    backgroundColor: "#fff",
    padding: "20px",
    borderRadius: "8px",
  },
  userInfo: {
    marginTop: "15px",
    lineHeight: "1.6",
  },
  taskHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "25px",
  },
  notificationHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "15px",
  },
  refreshButton: {
    backgroundColor: "#4285f4",
    color: "white",
    border: "none",
    padding: "8px 16px",
    borderRadius: "4px",
    cursor: "pointer",
  },
  error: {
    color: "#f44336",
    padding: "15px",
    backgroundColor: "#ffebee",
    borderRadius: "4px",
    marginBottom: "15px",
    border: "1px solid #ffcdd2",
  },
  loadingText: {
    textAlign: "center",
    padding: "20px",
    color: "#666",
  },
  emptyMessage: {
    textAlign: "center",
    padding: "30px 20px",
    color: "#666",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
    fontStyle: "italic",
  },
  taskGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
    gap: "20px",
  },
  taskCard: {
    padding: "20px",
    borderRadius: "8px",
    border: "1px solid #e0e0e0",
    backgroundColor: "#fafafa",
    cursor: "pointer",
    transition: "transform 0.2s, box-shadow 0.2s",
    boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
  taskCardCompleted: {
    backgroundColor: "#e8f5e9",
    borderColor: "#a5d6a7",
  },
  taskCardOverdue: {
    backgroundColor: "#ffebee",
    borderColor: "#ef9a9a",
  },
  taskTitle: {
    margin: "0 0 15px 0",
    fontSize: "18px",
    color: "#333",
  },
  taskMeta: {
    marginTop: "auto",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "14px",
  },
  taskDueDate: {
    fontWeight: "500",
    color: "#555",
  },
  taskDifficulty: {
    marginTop: "10px",
    fontSize: "13px",
    color: "#777",
    fontStyle: "italic",
  },
  statusBadgePending: {
    backgroundColor: "#fff3cd",
    color: "#856404",
    padding: "3px 10px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "600",
  },
  statusBadgeCompleted: {
    backgroundColor: "#d4edda",
    color: "#155724",
    padding: "3px 10px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "600",
  },
  statusBadgeOverdue: {
    backgroundColor: "#f8d7da",
    color: "#721c24",
    padding: "3px 10px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "600",
  },
  notificationList: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  notificationItem: {
    padding: "15px",
    borderRadius: "6px",
    border: "1px solid #e0e0e0",
  },
  notificationUnread: {
    backgroundColor: "#e8f0fe",
    borderLeft: "3px solid #4285f4",
  },
  notificationRead: {
    backgroundColor: "#fafafa",
  },
  notificationContent: {
    margin: "0 0 10px 0",
  },
  notificationMeta: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "12px",
    color: "#757575",
  },
  notificationDate: {
    fontStyle: "italic",
  },
  // Task Dialog Styles
  dialogOverlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 1000,
  },
  dialogContent: {
    backgroundColor: "white",
    borderRadius: "8px",
    padding: "30px",
    width: "90%",
    maxWidth: "600px",
    maxHeight: "90vh",
    overflowY: "auto",
    position: "relative",
    boxShadow: "0 5px 15px rgba(0, 0, 0, 0.3)",
  },
  closeButton: {
    position: "absolute",
    top: "15px",
    right: "15px",
    background: "none",
    border: "none",
    fontSize: "24px",
    color: "#999",
    cursor: "pointer",
  },
  dialogTitle: {
    marginTop: "0",
    marginBottom: "20px",
    color: "#333",
    borderBottom: "1px solid #eee",
    paddingBottom: "10px",
  },
  dialogInfo: {
    marginBottom: "25px",
  },
  dialogInfoRow: {
    marginBottom: "15px",
    display: "flex",
    alignItems: "flex-start",
  },
  dialogLabel: {
    fontWeight: "600",
    color: "#555",
    width: "100px",
    flexShrink: 0,
  },
  dialogActions: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "20px",
    borderTop: "1px solid #eee",
    paddingTop: "20px",
  },
  dialogOpenButton: {
    backgroundColor: "#4285f4",
    color: "white",
    padding: "10px 20px",
    borderRadius: "4px",
    textDecoration: "none",
    fontWeight: "500",
    textAlign: "center",
  },
  dialogCompleteButton: {
    backgroundColor: "#4caf50",
    color: "white",
    border: "none",
    padding: "10px 20px",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "500",
  },
  dialogResetButton: {
    backgroundColor: "#ff9800",
    color: "white",
    border: "none",
    padding: "10px 20px",
    borderRadius: "4px",
    cursor: "pointer",
    fontWeight: "500",
  },
  tagContainer: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  tag: {
    backgroundColor: "#e0e0e0",
    color: "#333",
    padding: "3px 8px",
    borderRadius: "12px",
    fontSize: "12px",
  },
  codeforcesLink: {
    color: "#4285f4",
    textDecoration: "none",
    fontWeight: "500",
  },
};

export default LearnerDashboard;