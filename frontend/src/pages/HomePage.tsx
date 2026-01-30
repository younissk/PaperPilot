import {
  SEO,
  HeroSection,
  ProofStrip,
  OutputPreview,
  HowItWorks,
  PrivacySection,
} from "@/components";

/**
 * Home page with hero, proof strip, output preview, how it works, and privacy sections.
 */
export default function HomePage() {
  return (
    <>
      <SEO
        title="From Query to Survey, with Citations"
        description="Get top papers, research angles, and open problems with traceable sources for every section. AI-powered literature review in seconds."
      />

      <main>
        {/* Hero Section */}
        <HeroSection />

        {/* Proof Strip - Trust Metrics */}
        <ProofStrip />

        {/* Output Preview */}
        <OutputPreview />

        {/* How It Works */}
        <HowItWorks />

        {/* Privacy Section */}
        <PrivacySection />
      </main>
    </>
  );
}
