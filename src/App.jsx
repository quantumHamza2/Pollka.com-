import { useEffect, useState } from "react";

function App() {
  const [results, setResults] = useState([]);

  // Fetch results from backend
  const getResults = async () => {
    try {
      const res = await fetch("http://localhost:8000/results");
      const data = await res.json();
      console.log("API DATA:", data); // debug
      setResults(data);
    } catch (err) {
      console.error("Error fetching results:", err);
    }
  };

  // Run allocation
  const runAllocation = async () => {
    try {
      await fetch("http://localhost:8000/allocate", {
        method: "POST",
      });

      alert("Allocation Completed");
      getResults(); // refresh after allocation
    } catch (err) {
      console.error("Error running allocation:", err);
    }
  };

  // Load on first render
  useEffect(() => {
    getResults();
  }, []);

  // Count allocated students
  const allocatedCount = results.filter(
    (s) => s.subject_name !== null
  ).length;

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🎓 Pollka Subject Allocation</h1>

      <button onClick={runAllocation} style={{ marginBottom: "20px" }}>
        Run Allocation
      </button>

      <h3>
        Allocated: {allocatedCount} / {results.length}
      </h3>

      <hr />

      {results.length === 0 ? (
        <p>No data found</p>
      ) : (
        results.map((student) => (
          <div
            key={student.student_id}
            style={{
              marginBottom: "12px",
              padding: "10px",
              border: "1px solid #ccc",
              borderRadius: "6px",
            }}
          >
            <strong>{student.student_name}</strong> ({student.cgpa})
            <br />

            {student.subject_name ? (
              <span style={{ color: "green" }}>
                ✅ {student.subject_name}
              </span>
            ) : (
              <span style={{ color: "red" }}>
                ❌ Not Allocated
              </span>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default App;