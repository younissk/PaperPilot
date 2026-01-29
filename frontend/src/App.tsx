import { createBrowserRouter, RouterProvider } from "react-router";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import AboutPage from "./pages/AboutPage";
import QueriesPage from "./pages/QueriesPage";
import ReportPage from "./pages/ReportPage";
import MonitoringPage from "./pages/MonitoringPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "about", element: <AboutPage /> },
      { path: "queries", element: <QueriesPage /> },
      { path: "report/:queryId", element: <ReportPage /> },
      { path: "monitoring", element: <MonitoringPage /> },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
