"""
YouTrack Issue Attachments Module.

This module contains functions for handling issue attachments and raw data access:
- Raw issue data retrieval bypassing Pydantic models
- Attachment content access with base64 encoding
- Comprehensive attachment metadata retrieval
- File size analysis and format conversion

These functions enable file handling and detailed data access within YouTrack workflows.
"""

import json
import base64
import logging
from typing import Any, Dict

from youtrack_mcp.api.issues import AttachmentNotFoundError
from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class Attachments:
    """Issue attachment and raw data access functions."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api
        self.client = issues_api.client  # Direct access for raw API calls

    @sync_wrapper
    def get_issue_raw(self, issue_id: str) -> str:
        """
        Get raw information about a specific issue, bypassing the Pydantic model.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")

        Returns:
            Raw JSON string with the issue data
        """
        try:
            # Request comprehensive fields for raw issue data
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value(id,name)),attachments(id,name,size,url),comments(id,text,author(login,name),created)"
            raw_issue = self.client.get(f"issues/{issue_id}?fields={fields}")
            return format_json_response(raw_issue)
        except Exception as e:
            logger.exception(f"Error getting raw issue {issue_id}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_attachment_content(self, issue_id: str, attachment_id: str) -> str:
        """
        Get the content of an attachment as a base64-encoded string.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            attachment_id: The attachment ID (e.g., "1-123")

        Returns:
            JSON string with the attachment content encoded in base64
        """
        try:
            content = self.issues_api.get_attachment_content(
                issue_id, attachment_id
            )
            encoded_content = base64.b64encode(content).decode("utf-8")

            # Get attachment metadata for additional info
            issue_response = self.client.get(
                f"issues/{issue_id}?fields=attachments(id,name,mimeType,size)"
            )
            attachment_metadata = None

            if "attachments" in issue_response:
                for attachment in issue_response["attachments"]:
                    if attachment.get("id") == attachment_id:
                        attachment_metadata = attachment
                        break

            return json.dumps(
                {
                    "content": encoded_content,
                    "size_bytes_original": len(content),
                    "size_bytes_base64": len(encoded_content),
                    "filename": (
                        attachment_metadata.get("name")
                        if attachment_metadata
                        else None
                    ),
                    "mime_type": (
                        attachment_metadata.get("mimeType")
                        if attachment_metadata
                        else None
                    ),
                    "size_increase_percent": round(
                        (len(encoded_content) / len(content) - 1) * 100, 1
                    ) if len(content) > 0 else 0.0,
                    "status": "success",
                }
            )
        except Exception as e:
            logger.exception(
                f"Error getting attachment content for issue {issue_id}, attachment {attachment_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def upload_attachment(
        self,
        issue_id: str,
        filename: str,
        content_base64: str,
        mime_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload an attachment to an issue from base64-encoded content.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            filename: Name to give the uploaded file (e.g., "screenshot.png")
            content_base64: The file content encoded as a base64 string
            mime_type: MIME type of the file (default: application/octet-stream)

        Returns:
            JSON string with the created attachment metadata
        """
        try:
            file_bytes = base64.b64decode(content_base64)
            attachment = self.issues_api.upload_attachment(
                issue_id, filename, file_bytes, mime_type
            )
            return format_json_response(
                {"status": "success", "attachment": attachment}
            )
        except Exception as e:
            logger.exception(
                f"Error uploading attachment to issue {issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def upload_comment_attachment(
        self,
        issue_id: str,
        comment_id: str,
        filename: str,
        content_base64: str,
        mime_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload an attachment to an existing comment on an issue.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            comment_id: The comment ID to attach the file to
            filename: Name to give the uploaded file (e.g., "log.txt")
            content_base64: The file content encoded as a base64 string
            mime_type: MIME type of the file (default: application/octet-stream)

        Returns:
            JSON string with the created attachment metadata
        """
        try:
            file_bytes = base64.b64decode(content_base64)
            attachment = self.issues_api.upload_comment_attachment(
                issue_id, comment_id, filename, file_bytes, mime_type
            )
            return format_json_response(
                {"status": "success", "attachment": attachment}
            )
        except Exception as e:
            logger.exception(
                f"Error uploading attachment to comment {comment_id} on issue {issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def delete_attachment(self, issue_id: str, attachment_id: str) -> str:
        """
        Delete an attachment from an issue.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            attachment_id: The attachment ID to delete (e.g., "1-123")

        Returns:
            JSON string with the deletion status
        """
        try:
            self.issues_api.delete_attachment(issue_id, attachment_id)
            return format_json_response({
                "status": "success",
                "message": f"Attachment {attachment_id} successfully deleted from issue {issue_id}"
            })
        except AttachmentNotFoundError as e:
            logger.warning(f"Attachment not found: {e}")
            return format_json_response({"error": str(e), "status": "not_found"})
        except Exception as e:
            logger.exception(
                f"Error deleting attachment {attachment_id} from issue {issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for attachment functions."""
        return {
            "get_issue_raw": {
                "description": "Get comprehensive raw issue data bypassing Pydantic models, including all fields, custom fields, attachments, and comments. Useful for detailed data analysis or when structured models are insufficient. Example: get_issue_raw(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "get_attachment_content": {
                "description": "Download and retrieve attachment content as base64-encoded data with comprehensive metadata including file size analysis and format information. Supports files up to 10MB. Example: get_attachment_content(issue_id='DEMO-123', attachment_id='1-456')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier containing the attachment like 'DEMO-123'",
                    "attachment_id": "Attachment identifier from issue attachments list like '1-456' or '2-789'"
                }
            },
            "delete_attachment": {
                "description": "Delete an attachment from an issue. Requires appropriate permissions (either being the attachment author or having 'Delete Attachment' permission in the project). The deletion is permanent. Example: delete_attachment(issue_id='DEMO-123', attachment_id='1-456')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier containing the attachment like 'DEMO-123'",
                    "attachment_id": "Attachment identifier to delete from issue attachments list like '1-456' or '2-789'"
                }
            },
            "upload_attachment": {
                "description": "Upload a file attachment to an issue. Expects base64-encoded file content. Example: upload_attachment(issue_id='DEMO-123', filename='screenshot.png', content_base64='iVBORw0KG...', mime_type='image/png')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier to attach the file to like 'DEMO-123'",
                    "filename": "Name to give the uploaded file, e.g. 'screenshot.png'",
                    "content_base64": "File content encoded as a base64 string",
                    "mime_type": "MIME type of the file, e.g. 'image/png' (default: application/octet-stream)"
                }
            },
            "upload_comment_attachment": {
                "description": "Upload a file attachment to an existing comment on an issue. Expects base64-encoded file content. Requires a comment_id: get one from add_comment's response (its 'id' field) when attaching to a comment you're creating now, or from get_issue_raw's comments list when attaching to an existing comment. Example: upload_comment_attachment(issue_id='DEMO-123', comment_id='4-56', filename='log.txt', content_base64='dGVzdA==', mime_type='text/plain')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier containing the comment like 'DEMO-123'",
                    "comment_id": "Comment identifier to attach the file to, e.g. '4-56'. Obtain it from add_comment's response or get_issue_raw's comments list",
                    "filename": "Name to give the uploaded file, e.g. 'log.txt'",
                    "content_base64": "File content encoded as a base64 string",
                    "mime_type": "MIME type of the file, e.g. 'text/plain' (default: application/octet-stream)"
                }
            }
        }