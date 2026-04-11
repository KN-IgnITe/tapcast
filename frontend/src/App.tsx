import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";

function App() {
  const [count, setCount] = useState(0);
  const [backendResponse, setBackendResponse] =
    useState<string>("No response yet");
  const [loading, setLoading] = useState(false);

  const callBackend = async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL;
      const response = await fetch(`${apiUrl}/ping`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      setBackendResponse(JSON.stringify(data, null, 2));
    } catch (error) {
      setBackendResponse(
        `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <button onClick={callBackend} disabled={loading}>
          {loading ? "Calling backend..." : "Call Backend"}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
        <div
          style={{ marginTop: "20px", padding: "10px", borderRadius: "4px" }}
        >
          <h3>Backend Response:</h3>
          <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {backendResponse}
          </pre>
        </div>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  );
}

export default App;
