import { useState, useEffect } from "react";
import axios from "axios";

// Chart components (using recharts)
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell 
} from "recharts";

const MentorStats = ({ learner, API_URL }) => {
  const [stats, setStats] = useState(null);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Colors for charts
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#A28BFC"];
  
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        // Fetch stats and summary data from database for the selected learner
        const statsResponse = await axios.get(
          `${API_URL}/ai/db/user/${learner.codeforces_handle}/stats`,
          { withCredentials: true }
        );
        
        const summaryResponse = await axios.get(
          `${API_URL}/ai/db/user/${learner.codeforces_handle}/summary`,
          { withCredentials: true }
        );
        
        setStats(statsResponse.data.stats);
        setSummary(summaryResponse.data.summary);
        setError(null);
      } catch (err) {
        console.error("Error fetching learner stats:", err);
        
        // Check if it's a 404 error (no data in database yet)
        if (err.response && err.response.status === 404) {
          setError("No statistics available for this learner in the database.");
        } else {
          setError("Failed to load this learner's progress statistics. Please try again later.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    if (learner?.codeforces_handle) {
      fetchStats();
    } else {
      setError("This learner doesn't have a Codeforces handle set up. Please ask them to update their profile.");
      setLoading(false);
    }
  }, [learner, API_URL]);
  
  // Convert difficulty distribution to array for chart
  const prepareDifficultyData = (distribution) => {
    if (!distribution) return [];
    
    return Object.entries(distribution).map(([name, value]) => ({
      name,
      value
    }));
  };
  
  // Convert tag distribution to array for chart
  const prepareTagData = (distribution) => {
    if (!distribution) return [];
    
    return Object.entries(distribution)
      .sort((a, b) => b[1] - a[1]) // Sort by count descending
      .slice(0, 5) // Get top 5 tags
      .map(([name, value]) => ({
        name,
        value
      }));
  };
  
  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner}></div>
        <p>Loading {learner.name}'s statistics...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div style={styles.errorContainer}>
        <h3>Oops!</h3>
        <p>{error}</p>
      </div>
    );
  }
  
  if (!stats || Object.keys(stats).length === 0) {
    return (
      <div style={styles.emptyState}>
        <h3>No Statistics Available</h3>
        <p>
          There are no statistics available for {learner.name} in the database.
        </p>
      </div>
    );
  }
  
  const difficultyData = prepareDifficultyData(stats.difficulty_distribution);
  const tagData = prepareTagData(stats.tag_distribution);
  
  return (
    <div style={styles.container}>
      <div style={styles.statsHeader}>
        <h2>{learner.name}'s Problem Solving Progress</h2>
        <div style={styles.totalSolved}>
          <span style={styles.solvedCount}>{stats.total_solved}</span>
          <span style={styles.solvedLabel}>problems solved this week</span>
        </div>
      </div>
      
      <div style={styles.summarySection}>
        <h3>Weekly Summary</h3>
        <div style={styles.summaryBox}>
          {summary ? (
            <p style={styles.summaryText}>{summary}</p>
          ) : (
            <p>No personalized summary available for this learner.</p>
          )}
        </div>
      </div>
      
      <div style={styles.chartsSection}>
        <div style={styles.chartContainer}>
          <h3>Problems by Difficulty</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={difficultyData}
                cx="50%"
                cy="50%"
                labelLine={true}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                nameKey="name"
                label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
              >
                {difficultyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`${value} problems`, ""]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        <div style={styles.chartContainer}>
          <h3>Top Problem Tags</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart
              data={tagData}
              margin={{ top: 5, right: 30, left: 20, bottom: 70 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={70}
                interval={0}
              />
              <YAxis allowDecimals={false} />
              <Tooltip formatter={(value) => [`${value} problems`, "Count"]} />
              <Bar dataKey="value" fill="#8884d8" name="Problems Solved" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div style={styles.progressSection}>
        <h3>Daily Progress</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart
            data={stats.progress_over_time}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis allowDecimals={false} />
            <Tooltip formatter={(value) => [`${value} problems`, "Problems Solved"]} />
            <Legend />
            <Bar 
              dataKey="problems_solved" 
              name="Problems Solved" 
              fill="#4285F4" 
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: "#fff",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 2px 10px rgba(0, 0, 0, 0.05)",
  },
  statsHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
    borderBottom: "1px solid #e0e0e0",
    paddingBottom: "15px",
  },
  totalSolved: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
  },
  solvedCount: {
    fontSize: "32px",
    fontWeight: "700",
    color: "#4285F4",
  },
  solvedLabel: {
    fontSize: "14px",
    color: "#666",
  },
  summarySection: {
    marginBottom: "30px",
  },
  summaryBox: {
    backgroundColor: "#f8f9fa",
    borderRadius: "8px",
    padding: "15px",
    border: "1px solid #e0e0e0",
  },
  summaryText: {
    lineHeight: "1.6",
    whiteSpace: "pre-wrap",
  },
  chartsSection: {
    display: "flex",
    gap: "20px",
    marginBottom: "30px",
    flexWrap: "wrap",
  },
  chartContainer: {
    flex: "1 1 45%",
    minWidth: "300px",
    backgroundColor: "#f8f9fa",
    borderRadius: "8px",
    padding: "15px",
    border: "1px solid #e0e0e0",
  },
  progressSection: {
    backgroundColor: "#f8f9fa",
    borderRadius: "8px",
    padding: "15px",
    border: "1px solid #e0e0e0",
  },
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    height: "300px",
    color: "#555",
  },
  spinner: {
    border: "4px solid rgba(0, 0, 0, 0.1)",
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    borderLeftColor: "#4285F4",
    marginBottom: "15px",
    animation: "spin 1s linear infinite",
  },
  errorContainer: {
    textAlign: "center",
    padding: "40px 20px",
    backgroundColor: "#fff3f3",
    borderRadius: "8px",
    border: "1px solid #ffcfcf",
  },
  emptyState: {
    textAlign: "center",
    padding: "40px 20px",
    backgroundColor: "#f5f7ff",
    borderRadius: "8px",
    border: "1px solid #dce4ff",
  },
  // Add spin animation for the loading spinner
  '@keyframes spin': {
    '0%': { transform: 'rotate(0deg)' },
    '100%': { transform: 'rotate(360deg)' }
  }
};

export default MentorStats;