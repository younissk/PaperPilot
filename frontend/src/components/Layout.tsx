import { Outlet } from "react-router";
import { Header } from "./Header";

/**
 * Main layout component wrapping all pages.
 */
export default function Layout() {
  return (
    <>
      <Header />
      <main className="min-h-[calc(100vh-3.5rem)] p-6">
        <Outlet />
      </main>
    </>
  );
}
