import { Outlet } from "react-router";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { CustomCursor } from "./CustomCursor";

/**
 * Main layout component wrapping all pages.
 * Brutalist minimal design with transparent header, minimal footer, and custom cursor.
 */
export default function Layout() {
  return (
    <>
      <CustomCursor />
      <Header />
      <main>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
