"""PaperPilot - AI-powered academic literature discovery.

This is the main entry point. Use the CLI for the best experience:
    paperpilot search "your research query"
    paperpilot results snowball_results.json
"""

from paperpilot.cli.app import app

if __name__ == "__main__":
    app()
