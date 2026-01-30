"""Email notification helpers using Azure Communication Services."""

from __future__ import annotations

from typing import Any

from .config import ACS_CONNECTION_STRING, ACS_SENDER_ADDRESS, FRONTEND_BASE_URL, logger


def _slugify(query: str) -> str:
    """Convert query to URL-safe slug (matching frontend slugifyQuery)."""
    slug = query.lower()
    # Remove non-word characters except spaces and hyphens
    slug = "".join(c if c.isalnum() or c in " -" else "" for c in slug)
    # Replace spaces and hyphens with underscores
    slug = "_".join(slug.split())
    slug = slug.replace("-", "_")
    # Trim underscores from ends
    slug = slug.strip("_")
    # Limit length
    if len(slug) > 100:
        slug = slug[:100]
    return slug


def _build_report_url(query: str, job_id: str) -> str:
    """Build the full URL to the report page."""
    slug = _slugify(query)
    return f"{FRONTEND_BASE_URL}/report/{slug}?job={job_id}"


def _completion_email_html(query: str, job_id: str, report_url: str, result: dict[str, Any]) -> str:
    """Generate HTML content for completion email."""
    papers_found = result.get("papers_found", 0)
    papers_ranked = result.get("papers_ranked", 0)
    report_sections = result.get("report_sections", 0)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Your Research Report is Ready!</h1>
    </div>
    
    <div style="background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="margin-top: 0;">Great news! Your PaperPilot research report has been completed.</p>
        
        <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="margin: 0 0 10px 0;"><strong>Query:</strong> {query}</p>
            <p style="margin: 0 0 10px 0;"><strong>Papers Found:</strong> {papers_found}</p>
            <p style="margin: 0 0 10px 0;"><strong>Papers Ranked:</strong> {papers_ranked}</p>
            <p style="margin: 0;"><strong>Report Sections:</strong> {report_sections}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{report_url}" style="display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600;">View Your Report</a>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin-bottom: 0;">
            If the button doesn't work, copy and paste this link into your browser:<br>
            <a href="{report_url}" style="color: #667eea; word-break: break-all;">{report_url}</a>
        </p>
    </div>
    
    <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
        <p style="margin: 0;">Sent by <a href="{FRONTEND_BASE_URL}" style="color: #667eea;">PaperPilot</a></p>
        <p style="margin: 5px 0 0 0;">Intelligent Academic Paper Discovery</p>
    </div>
</body>
</html>"""


def _completion_email_text(query: str, job_id: str, report_url: str, result: dict[str, Any]) -> str:
    """Generate plain text content for completion email."""
    papers_found = result.get("papers_found", 0)
    papers_ranked = result.get("papers_ranked", 0)
    report_sections = result.get("report_sections", 0)

    return f"""Your Research Report is Ready!

Great news! Your PaperPilot research report has been completed.

Query: {query}
Papers Found: {papers_found}
Papers Ranked: {papers_ranked}
Report Sections: {report_sections}

View your report here:
{report_url}

---
Sent by PaperPilot - Intelligent Academic Paper Discovery
{FRONTEND_BASE_URL}
"""


def _failure_email_html(query: str, job_id: str, error: str) -> str:
    """Generate HTML content for failure email."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #ef4444; padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Research Report Failed</h1>
    </div>
    
    <div style="background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="margin-top: 0;">Unfortunately, we encountered an error while generating your research report.</p>
        
        <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="margin: 0 0 10px 0;"><strong>Query:</strong> {query}</p>
            <p style="margin: 0 0 10px 0;"><strong>Job ID:</strong> {job_id}</p>
            <p style="margin: 0; color: #ef4444;"><strong>Error:</strong> {error}</p>
        </div>
        
        <p>Please try submitting your query again. If the problem persists, the issue may be temporary.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{FRONTEND_BASE_URL}" style="display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600;">Try Again</a>
        </div>
    </div>
    
    <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
        <p style="margin: 0;">Sent by <a href="{FRONTEND_BASE_URL}" style="color: #667eea;">PaperPilot</a></p>
        <p style="margin: 5px 0 0 0;">Intelligent Academic Paper Discovery</p>
    </div>
</body>
</html>"""


def _failure_email_text(query: str, job_id: str, error: str) -> str:
    """Generate plain text content for failure email."""
    return f"""Research Report Failed

Unfortunately, we encountered an error while generating your research report.

Query: {query}
Job ID: {job_id}
Error: {error}

Please try submitting your query again. If the problem persists, the issue may be temporary.

Visit PaperPilot to try again:
{FRONTEND_BASE_URL}

---
Sent by PaperPilot - Intelligent Academic Paper Discovery
"""


def send_completion_email(
    to_email: str,
    query: str,
    job_id: str,
    result: dict[str, Any],
) -> bool:
    """Send a completion notification email.

    Args:
        to_email: Recipient email address
        query: The research query that was processed
        job_id: The job identifier
        result: The job result containing papers_found, papers_ranked, etc.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not ACS_CONNECTION_STRING:
        logger.warning("ACS not configured, skipping completion email to %s", to_email)
        return False

    if not to_email:
        logger.debug("No notification email provided, skipping")
        return False

    try:
        from azure.communication.email import EmailClient

        report_url = _build_report_url(query, job_id)

        email_client = EmailClient.from_connection_string(ACS_CONNECTION_STRING)

        message = {
            "senderAddress": ACS_SENDER_ADDRESS,
            "recipients": {
                "to": [{"address": to_email}],
            },
            "content": {
                "subject": f"Your PaperPilot Report is Ready: {query[:50]}{'...' if len(query) > 50 else ''}",
                "plainText": _completion_email_text(query, job_id, report_url, result),
                "html": _completion_email_html(query, job_id, report_url, result),
            },
        }

        poller = email_client.begin_send(message)
        result_status = poller.result()

        logger.info("Completion email sent to %s, message_id=%s", to_email, result_status.get("id", "unknown"))
        return True

    except Exception as exc:
        logger.error("Failed to send completion email to %s: %s", to_email, exc)
        return False


def send_failure_email(
    to_email: str,
    query: str,
    job_id: str,
    error: str,
) -> bool:
    """Send a failure notification email.

    Args:
        to_email: Recipient email address
        query: The research query that was processed
        job_id: The job identifier
        error: The error message

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not ACS_CONNECTION_STRING:
        logger.warning("ACS not configured, skipping failure email to %s", to_email)
        return False

    if not to_email:
        logger.debug("No notification email provided, skipping")
        return False

    try:
        from azure.communication.email import EmailClient

        email_client = EmailClient.from_connection_string(ACS_CONNECTION_STRING)

        message = {
            "senderAddress": ACS_SENDER_ADDRESS,
            "recipients": {
                "to": [{"address": to_email}],
            },
            "content": {
                "subject": f"PaperPilot Report Failed: {query[:50]}{'...' if len(query) > 50 else ''}",
                "plainText": _failure_email_text(query, job_id, error),
                "html": _failure_email_html(query, job_id, error),
            },
        }

        poller = email_client.begin_send(message)
        result_status = poller.result()

        logger.info("Failure email sent to %s, message_id=%s", to_email, result_status.get("id", "unknown"))
        return True

    except Exception as exc:
        logger.error("Failed to send failure email to %s: %s", to_email, exc)
        return False
