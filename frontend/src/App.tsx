import { createBrowserRouter, RouterProvider } from "react-router";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import QueriesPage from "./pages/QueriesPage";
import ReportPage from "./pages/ReportPage";
import MonitoringPage from "./pages/MonitoringPage";

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <Layout />,
      children: [
        { index: true, element: <HomePage /> },
        { path: "queries", element: <QueriesPage /> },
        { path: "report/:queryId", element: <ReportPage /> },
        { path: "monitoring", element: <MonitoringPage /> },
      ],
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  },
);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
