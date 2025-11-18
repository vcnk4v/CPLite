// import { useState, useEffect } from "react";
// import { useAuth } from "../contexts/AuthContext";
// import axios from "axios";

// // Ensure your API_URL points to the gateway or the base URL where
// // both task and notification services are routed.
// const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// const Dashboard = () => {
//   const { user, logout } = useAuth();
//   console.log("User data:", user);
//   console.log("HEYYY");
//   // Existing Task State
//   const [tasks, setTasks] = useState([]);
//   const [tasksLoading, setTasksLoading] = useState(false);
//   const [tasksError, setTasksError] = useState("");

//   // New Notification State
//   const [notifications, setNotifications] = useState([]);
//   const [notificationsLoading, setNotificationsLoading] = useState(false);
//   const [notificationsError, setNotificationsError] = useState("");

//   const [activeTab, setActiveTab] = useState("profile"); // Default tab

//   // Fetch data based on active tab when user or activeTab changes
//   useEffect(() => {
//     if (!user) return; // Don't fetch if user is not loaded

//     if (activeTab === "tasks") {
//       fetchTasks();
//     } else if (activeTab === "notifications") {
//       fetchNotifications();
//     }
//     // No fetch needed for 'profile' as data comes from useAuth
//   }, [user, activeTab]); // Rerun effect if user or activeTab changes

//   const fetchTasks = async () => {
//     if (!user) return;
//     setTasksLoading(true);
//     setTasksError("");
//     try {
//       // Assuming task endpoint is /tasks/user/:userId
//       const response = await axios.get(`${API_URL}/tasks/user/${user.id}`);
//       setTasks(response.data);
//     } catch (err) {
//       console.error("Error fetching tasks:", err);
//       setTasksError(
//         "Failed to load tasks. Check service availability and authentication."
//       );
//     } finally {
//       setTasksLoading(false);
//     }
//   };

//   // New function to fetch notifications
//   const fetchNotifications = async () => {
//     if (!user) return;
//     setNotificationsLoading(true);
//     setNotificationsError("");
//     try {
//       // *** IMPORTANT: Adjust this URL based on your notification service API route ***
//       const response = await axios.get(
//         `${API_URL}/notification/user/${user.id}`
//       );
//       // Sort notifications by creation date, newest first
//       const sortedNotifications = response.data.sort(
//         (a, b) => new Date(b.created_at) - new Date(a.created_at)
//       );
//       setNotifications(sortedNotifications);
//     } catch (err) {
//       console.error("Error fetching notifications:", err);
//       setNotificationsError(
//         "Failed to load notifications. Check service availability and authentication."
//       );
//     } finally {
//       setNotificationsLoading(false);
//     }
//   };

//   const updateTaskStatus = async (taskId, newStatus) => {
//     try {
//       await axios.put(`${API_URL}/tasks/${taskId}`, { status: newStatus });
//       setTasks(
//         tasks.map((task) =>
//           task.id === taskId ? { ...task, status: newStatus } : task
//         )
//       );
//     } catch (err) {
//       console.error("Error updating task:", err);
//       alert("Failed to update task status");
//     }
//   };

//   // TODO: Implement function to mark notifications as read if needed
//   // const markNotificationAsRead = async (notificationId) => { ... }

//   if (!user) {
//     return <div>Loading user data...</div>;
//   }

//   const formatDate = (dateString) => {
//     if (!dateString) return "N/A";
//     const date = new Date(dateString);
//     return date.toLocaleDateString() + " " + date.toLocaleTimeString();
//   };

//   return (
//     <div style={styles.container}>
//       <div style={styles.header}>
//         <h1>CPLite Dashboard</h1>
//         <button onClick={logout} style={styles.logoutButton}>
//           Logout
//         </button>
//       </div>

//       {/* --- Tabs --- */}
//       <div style={styles.tabs}>
//         <button
//           style={
//             activeTab === "profile"
//               ? { ...styles.tabButton, ...styles.activeTab }
//               : styles.tabButton
//           }
//           onClick={() => setActiveTab("profile")}
//         >
//           Profile
//         </button>
//         <button
//           style={
//             activeTab === "tasks"
//               ? { ...styles.tabButton, ...styles.activeTab }
//               : styles.tabButton
//           }
//           onClick={() => setActiveTab("tasks")}
//         >
//           Tasks
//         </button>
//         {/* --- New Notifications Tab Button --- */}
//         <button
//           style={
//             activeTab === "notifications"
//               ? { ...styles.tabButton, ...styles.activeTab }
//               : styles.tabButton
//           }
//           onClick={() => setActiveTab("notifications")}
//         >
//           Notifications
//           {/* Optional: Add a badge for unread notifications */}
//           {/* {notifications.filter(n => !n.is_read).length > 0 && (
//              <span style={styles.notificationBadge}>
//                {notifications.filter(n => !n.is_read).length}
//              </span>
//            )} */}
//         </button>
//       </div>

//       {/* --- Profile Tab Content --- */}
//       {activeTab === "profile" && (
//         <div style={styles.card}>
//           <h2>User Profile</h2>
//           <div style={styles.userInfo}>
//             <p>
//               <strong>Name:</strong> {user.name}
//             </p>
//             <p>
//               <strong>Email:</strong> {user.email}
//             </p>
//             <p>
//               <strong>Role:</strong> {user.role}
//             </p>
//             <p>
//               <strong>User ID:</strong> {user.id}
//             </p>
//             {user.codeforces_handle && (
//               <p>
//                 <strong>Codeforces Handle:</strong> {user.codeforces_handle}
//               </p>
//             )}
//           </div>
//         </div>
//       )}

//       {/* --- Tasks Tab Content --- */}
//       {activeTab === "tasks" && (
//         <div style={styles.card}>
//           <div style={styles.taskHeader}>
//             <h2>Your Tasks</h2>
//             <button
//               onClick={fetchTasks} // Refetch tasks specifically
//               style={styles.refreshButton}
//               disabled={tasksLoading}
//             >
//               {tasksLoading ? "Refreshing..." : "Refresh Tasks"}
//             </button>
//           </div>

//           {tasksLoading && <p>Loading tasks...</p>}

//           {tasksError && (
//             <div style={styles.error}>
//               <p>{tasksError}</p>
//               {/* Optional more specific message */}
//               {/* <p>Ensure the task service is running and CORS/JWT settings match the auth service.</p> */}
//             </div>
//           )}

//           {!tasksLoading && !tasksError && tasks.length === 0 && (
//             <p>No tasks found.</p>
//           )}

//           {!tasksLoading && !tasksError && tasks.length > 0 && (
//             <div style={styles.taskList}>
//               {tasks.map((task) => (
//                 <div key={task.id} style={styles.taskItem}>
//                   {/* ... (keep existing task rendering logic) ... */}
//                   <div style={styles.taskDetails}>
//                     <h3>{task.title}</h3>
//                     {task.description && <p>{task.description}</p>}
//                     <div style={styles.taskMeta}>
//                       <p>
//                         <strong>Due:</strong> {formatDate(task.due_date)}
//                       </p>
//                       <p>
//                         <strong>Status:</strong>
//                         <select
//                           value={task.status}
//                           onChange={(e) =>
//                             updateTaskStatus(task.id, e.target.value)
//                           }
//                           style={{
//                             ...styles.statusSelect,
//                             backgroundColor:
//                               task.status === "completed"
//                                 ? "#e6f7e6"
//                                 : task.status === "overdue"
//                                 ? "#f7e6e6"
//                                 : "#fff",
//                           }}
//                         >
//                           <option value="pending">Pending</option>
//                           <option value="completed">Completed</option>
//                           <option value="overdue">Overdue</option>
//                         </select>
//                       </p>
//                     </div>
//                     {task.url && (
//                       <a
//                         href={task.url}
//                         target="_blank"
//                         rel="noopener noreferrer"
//                         style={styles.taskLink}
//                       >
//                         Open Problem
//                       </a>
//                     )}
//                   </div>
//                 </div>
//               ))}
//             </div>
//           )}
//         </div>
//       )}

//       {/* --- New Notifications Tab Content --- */}
//       {activeTab === "notifications" && (
//         <div style={styles.card}>
//           <div style={styles.notificationHeader}>
//             {" "}
//             {/* Use specific header style */}
//             <h2>Notifications</h2>
//             <button
//               onClick={fetchNotifications} // Refetch notifications specifically
//               style={styles.refreshButton}
//               disabled={notificationsLoading}
//             >
//               {notificationsLoading ? "Refreshing..." : "Refresh Notifications"}
//             </button>
//           </div>

//           {notificationsLoading && <p>Loading notifications...</p>}

//           {notificationsError && (
//             <div style={styles.error}>
//               <p>{notificationsError}</p>
//               {/* Optional more specific message */}
//               {/* <p>Ensure the notification service is running and CORS/JWT settings match the auth service.</p> */}
//             </div>
//           )}

//           {!notificationsLoading &&
//             !notificationsError &&
//             notifications.length === 0 && <p>You have no new notifications.</p>}

//           {!notificationsLoading &&
//             !notificationsError &&
//             notifications.length > 0 && (
//               <div style={styles.notificationList}>
//                 {" "}
//                 {/* Use specific list style */}
//                 {notifications.map((notification) => (
//                   <div
//                     key={notification.id}
//                     style={{
//                       ...styles.notificationItem, // Use specific item style
//                       ...(notification.is_read
//                         ? styles.notificationRead
//                         : styles.notificationUnread), // Style based on read status
//                     }}
//                   >
//                     <p style={styles.notificationContent}>
//                       {notification.content}
//                     </p>
//                     <div style={styles.notificationMeta}>
//                       <span style={styles.notificationDate}>
//                         {formatDate(notification.created_at)}
//                       </span>
//                       {/* Optional: Add button to mark as read */}
//                       {/* {!notification.is_read && (
//                        <button
//                          onClick={() => markNotificationAsRead(notification.id)}
//                          style={styles.markReadButton}
//                        >
//                          Mark as Read
//                        </button>
//                      )} */}
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             )}
//         </div>
//       )}
//     </div>
//   );
// };

// // --- Styles ---
// // (Keep existing styles and add new ones for notifications)
// const styles = {
//   container: {
//     padding: "20px",
//     maxWidth: "900px", // Maybe increase max width slightly
//     margin: "0 auto",
//     fontFamily: "sans-serif", // Basic font
//   },
//   header: {
//     display: "flex",
//     justifyContent: "space-between",
//     alignItems: "center",
//     marginBottom: "20px",
//     paddingBottom: "10px",
//     borderBottom: "1px solid #eee",
//   },
//   logoutButton: {
//     backgroundColor: "#f44336",
//     color: "white",
//     border: "none",
//     padding: "8px 16px",
//     borderRadius: "4px",
//     cursor: "pointer",
//     transition: "background-color 0.2s",
//   },
//   logoutButtonHover: {
//     // Example hover state (add logic if needed)
//     backgroundColor: "#d32f2f",
//   },
//   tabs: {
//     display: "flex",
//     marginBottom: "20px",
//     borderBottom: "1px solid #ddd",
//   },
//   tabButton: {
//     padding: "10px 20px",
//     border: "none",
//     background: "none",
//     cursor: "pointer",
//     fontSize: "16px",
//     borderBottom: "3px solid transparent",
//     color: "#555",
//     transition: "color 0.2s, border-bottom-color 0.2s",
//   },
//   activeTab: {
//     borderBottom: "3px solid #4285F4",
//     fontWeight: "bold",
//     color: "#000",
//   },
//   card: {
//     backgroundColor: "#fff",
//     borderRadius: "8px",
//     padding: "25px",
//     boxShadow: "0 2px 5px rgba(0, 0, 0, 0.1)",
//     marginTop: "10px",
//   },
//   userInfo: {
//     lineHeight: "1.6",
//   },
//   taskHeader: {
//     // Keep specific header styles if needed
//     display: "flex",
//     justifyContent: "space-between",
//     alignItems: "center",
//     marginBottom: "20px",
//     paddingBottom: "10px",
//     borderBottom: "1px dashed #eee",
//   },
//   notificationHeader: {
//     // Style for notification header
//     display: "flex",
//     justifyContent: "space-between",
//     alignItems: "center",
//     marginBottom: "20px",
//     paddingBottom: "10px",
//     borderBottom: "1px dashed #eee",
//   },
//   refreshButton: {
//     backgroundColor: "#4285F4",
//     color: "white",
//     border: "none",
//     padding: "8px 15px",
//     borderRadius: "4px",
//     cursor: "pointer",
//     fontSize: "14px",
//     transition: "background-color 0.2s",
//   },
//   refreshButtonHover: {
//     // Example hover state
//     backgroundColor: "#3367D6",
//   },
//   taskList: {
//     // Keep task list styles
//     display: "flex",
//     flexDirection: "column",
//     gap: "15px",
//   },
//   taskItem: {
//     // Keep task item styles
//     padding: "15px",
//     borderRadius: "4px",
//     border: "1px solid #e0e0e0",
//     backgroundColor: "#f9f9f9",
//   },
//   taskDetails: {
//     display: "flex",
//     flexDirection: "column",
//     gap: "10px",
//   },
//   taskMeta: {
//     display: "flex",
//     justifyContent: "space-between",
//     alignItems: "center",
//     fontSize: "14px",
//     color: "#555",
//   },
//   statusSelect: {
//     padding: "4px 8px",
//     borderRadius: "3px",
//     marginLeft: "8px",
//     border: "1px solid #ccc",
//   },
//   taskLink: {
//     display: "inline-block",
//     backgroundColor: "#4CAF50", // Changed color for variety
//     color: "white",
//     padding: "6px 12px",
//     borderRadius: "4px",
//     textDecoration: "none",
//     fontSize: "14px",
//     alignSelf: "flex-start",
//     marginTop: "5px",
//     transition: "background-color 0.2s",
//   },
//   taskLinkHover: {
//     backgroundColor: "#45a049",
//   },
//   error: {
//     backgroundColor: "#FFF3F3",
//     padding: "15px",
//     borderRadius: "4px",
//     border: "1px solid #FFD7D7",
//     color: "#D32F2F",
//     marginBottom: "15px",
//     lineHeight: "1.5",
//   },

//   // --- New Notification Styles ---
//   notificationList: {
//     display: "flex",
//     flexDirection: "column",
//     gap: "12px",
//   },
//   notificationItem: {
//     padding: "12px 15px",
//     borderRadius: "4px",
//     border: "1px solid #e0e0e0",
//     transition: "background-color 0.2s",
//   },
//   notificationUnread: {
//     backgroundColor: "#f9f9f9", // Slightly different background for unread
//     fontWeight: "bold", // Make unread text bold
//   },
//   notificationRead: {
//     backgroundColor: "#fff",
//     color: "#555", // Dim read notifications slightly
//     fontWeight: "normal",
//   },
//   notificationContent: {
//     margin: "0 0 8px 0", // Space below content
//     lineHeight: "1.5",
//   },
//   notificationMeta: {
//     display: "flex",
//     justifyContent: "space-between",
//     alignItems: "center",
//     fontSize: "13px",
//     color: "#777",
//   },
//   notificationDate: {
//     fontStyle: "italic",
//   },
//   markReadButton: {
//     // Optional style for a mark-as-read button
//     marginLeft: "10px",
//     padding: "3px 8px",
//     fontSize: "12px",
//     cursor: "pointer",
//     backgroundColor: "#eee",
//     border: "1px solid #ccc",
//     borderRadius: "3px",
//   },
//   notificationBadge: {
//     // Optional style for unread count badge
//     display: "inline-block",
//     marginLeft: "8px",
//     backgroundColor: "red",
//     color: "white",
//     borderRadius: "50%",
//     padding: "2px 6px",
//     fontSize: "10px",
//     lineHeight: "1",
//     verticalAlign: "middle",
//   },
// };

// export default Dashboard;

// src/components/Dashboard.jsx
import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import axios from "axios"; // Keep axios if needed elsewhere, but specific fetches move
import MentorDashboard from "./MentorDashboard";
import LearnerDashboard from "./LearnerDashboard"; // Assuming you'll create/update this later

// API URL remains the same
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const Dashboard = () => {
  const { user, logout } = useAuth();

  // No need for task/notification state here anymore

  if (!user) {
    // Enhanced loading state
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner}></div>
        <p>Loading user data...</p>
      </div>
    );
  }

  // Determine user role
  const isMentor = user.role === "mentor";

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>CPLite Dashboard</h1>
        <div style={styles.headerRight}>
          <span style={styles.userRole}>{isMentor ? "Mentor" : "Learner"}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </div>

      {/* Conditionally render the specific dashboard based on role */}
      {isMentor ? (
        // Pass API_URL and user to MentorDashboard
        <MentorDashboard user={user} API_URL={API_URL} />
      ) : (
        // Pass API_URL and user to LearnerDashboard (implement later)
        <LearnerDashboard user={user} API_URL={API_URL} />
      )}
    </div>
  );
};

// --- Styles --- (Keep relevant styles, add loading style)
const styles = {
  container: {
    padding: "20px 30px", // Slightly more horizontal padding
    maxWidth: "1100px", // Wider for potentially more complex dashboards
    margin: "20px auto",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif", // A common modern font
    backgroundColor: "#f9f9f9", // Light background for the whole page
    minHeight: "calc(100vh - 40px)", // Ensure it takes height
    boxSizing: 'border-box',
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "30px",
    paddingBottom: "15px",
    borderBottom: "2px solid #e0e0e0", // Slightly thicker border
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: "20px", // Increased gap
  },
  userRole: {
    backgroundColor: "#e0e0e0", // Neutral gray
    color: "#333",
    padding: "6px 12px",
    borderRadius: "15px", // More rounded
    fontSize: "14px",
    fontWeight: "600", // Semibold
    textTransform: "capitalize",
  },
  logoutButton: {
    backgroundColor: "#dc3545", // Bootstrap danger red
    color: "white",
    border: "none",
    padding: "8px 18px",
    borderRadius: "5px",
    cursor: "pointer",
    fontSize: '15px',
    fontWeight: '500',
    transition: "background-color 0.2s ease-in-out, transform 0.1s ease",
    ':hover': { // Add hover pseudo-class handling if using styled-components or similar
        backgroundColor: "#c82333",
    },
    ':active': {
        transform: 'scale(0.98)',
    }
  },
  loadingContainer: {
    display: "flex",
    flexDirection: "column", // Stack spinner and text
    justifyContent: "center",
    alignItems: "center",
    height: "80vh", // Use viewport height
    color: "#555",
    fontSize: '18px',
  },
   spinner: { // Simple CSS spinner
    border: '4px solid rgba(0, 0, 0, 0.1)',
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    borderLeftColor: '#4285F4', // Google Blue
    marginBottom: '15px', // Space between spinner and text
    animation: 'spin 1s linear infinite',
  },
  // Keyframes for spinner animation needs to be defined globally or via CSS-in-JS library features
  // @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  // Add this keyframe rule to your global CSS or index.css
};


export default Dashboard;