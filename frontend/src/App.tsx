const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export default function App() {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", margin: "2rem" }}>
      <h1>Village Vehicle Tracking</h1>
      <p>Frontend scaffold is running. API base URL: {apiBaseUrl}</p>
    </main>
  );
}
