import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";
import regradeIcon from './icons/regrade-icon.svg';

const App = () => {
  const [selectedReviewer, setSelectedReviewer] = useState("");
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [unassignedAlert, setUnassignedAlert] = useState(false);

  const reviewers = ["Alejandro", "Tuan", "Nhung", "Shahriar", "Tomer", "NotAssigned"];
  const base_url = "http://localhost:5000";

  useEffect(() => {
    // Check for unassigned students on component mount
    const checkUnassignedAlert = async () => {
      try {
        const response = await axios.get(`${base_url}/unassigned_alert`);
        setUnassignedAlert(response.data.alert);
      } catch (error) {
        console.error("Failed to fetch unassigned alert", error);
      }
    };
    checkUnassignedAlert();
  }, []);

  const fetchCodioData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${base_url}/scrape_assignments`);
      console.log("Codio data fetched:", response.data);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      setError("Failed to fetch Codio data");
      console.error("Codio fetch error:", error);
    }
  };

  const parseDate = (dateString) => {
    const cleanDateString = dateString.replace(/(\d+)(st|nd|rd|th)/, "$1");
    return new Date(cleanDateString);
  };

  const fetchAssignments = async () => {
    if (!selectedReviewer) {
      setError("Please select a reviewer");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${base_url}/exercises_per_reviewer/${selectedReviewer}`
      );

      const sortedAssignments = response.data.data.sort((a, b) => {
        const dateA = parseDate(a.completed_date);
        const dateB = parseDate(b.completed_date);
        return dateA - dateB;
      });

      setAssignments(sortedAssignments);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      setError("Failed to load exercises");
      console.error("Exercise fetch error:", error);
    }
  };

  const handleReviewerChange = (e) => {
    setSelectedReviewer(e.target.value);
    setAssignments([]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Reviewer Dashboard</h1>
        <div className="actions">
          <button onClick={fetchCodioData}>Fetch Codio Data</button>
          <select
            value={selectedReviewer}
            onChange={handleReviewerChange}
          >
            <option value="">Select Reviewer</option>
            {reviewers.map((reviewer, index) => (
              <option key={index} value={reviewer}>
                {reviewer}
              </option>
            ))}
          </select>
          <button onClick={fetchAssignments}>Load Exercises</button>
        </div>
      </header>

      <div className="exercise-count">
        {assignments.length > 0 && (
          <p>Total Exercises for {selectedReviewer}: <span>{assignments.length}</span></p>
        )}
        {unassignedAlert && (
          <p className="alert">⚠️ There are unassigned students</p>
        )}
      </div>

      <div className="assignments-table">
        {loading && <p>Loading...</p>}
        {error && <p className="error">{error}</p>}
        {!loading && assignments.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Student Name</th>
                <th>Exercise Name</th>
                <th>Time</th>
                <th>Reviewer</th>
              </tr>
            </thead>
            <tbody>
              {assignments.map((assignment, index) => (
                <tr key={index} style={{ backgroundColor: assignment.color }}>
                  <td>{assignment.name}</td>
                  <td>
                    {assignment.assignment_name}
                    {assignment.regrade && (
                      <img
                        src={regradeIcon}
                        alt="Regrade Request"
                        title="Regrade Request"
                        style={{ marginLeft: "8px", width: "20px", verticalAlign: "middle" }}
                      />
                    )}
                  </td>
                  <td>{assignment.completed_date}</td>
                  <td>{selectedReviewer}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default App;
