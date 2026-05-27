import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import JobsPage from "./pages/JobsPage";
import ScrapersPage from "./pages/ScrapersPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/jobs" replace />} />
        <Route path="scrapers" element={<ScrapersPage />} />
        <Route path="jobs" element={<JobsPage />} />
      </Route>
    </Routes>
  );
}
