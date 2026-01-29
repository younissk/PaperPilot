import { SEO, SearchForm } from "@/components";

/**
 * Home page with search form.
 */
export default function HomePage() {
  return (
    <>
      <SEO
        title="Discover Research Papers"
        description="Use Paper Navigator's intelligent snowball search to find and explore relevant academic papers."
      />

      <div className="min-h-[calc(100vh-55px-3rem)] flex items-center justify-center">
        <div className="container container-lg">
          <SearchForm />
        </div>
      </div>
    </>
  );
}
