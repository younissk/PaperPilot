import {
  SEO,
  HeroSection,
  ProofStrip,
  OutputPreview,
  HowItWorks,
  AboutSection,
  InfrastructureSection,
  PrivacySection,
} from "@/components";

/**
 * Home page with hero, proof strip, how it works, output preview, about, and privacy sections.
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

        {/* How It Works */}
        <HowItWorks />

        {/* Output Preview */}
        <OutputPreview />

        {/* About Section */}
        <AboutSection />

        {/* Infrastructure Section */}
        <InfrastructureSection />

        {/* Privacy Section */}
        <PrivacySection />
      </main>
    </>
  );
}
