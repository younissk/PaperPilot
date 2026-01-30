import { Outlet } from "react-router";
import { Header } from "./Header";
import { Footer } from "./Footer";

/**
 * Main layout component wrapping all pages.
 * Brutalist minimal design with transparent header and minimal footer.
 */
export default function Layout() {
  return (
    <>
      <Header />
      <main>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
