"""MIME email builder for Gmail-compatible HTML with embedded images."""

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate
from typing import Dict, Optional
import re


class MimeEmailBuilder:
    """Build MIME emails with embedded images for Gmail compatibility."""
    
    def __init__(self):
        """Initialize the MIME builder."""
        pass
    
    def build_gmail_text_email(self, text: str, images: Dict[str, tuple], 
                               subject: str = "LaTeX Email",
                               from_addr: Optional[str] = None,
                               to_addr: Optional[str] = None) -> MIMEMultipart:
        """Build a Gmail-compatible text email with inline image references.
        
        Args:
            text: Text with image placeholders
            images: Dict mapping placeholder IDs to (bytes, width, height, depth)
            subject: Email subject
            from_addr: From address (optional)
            to_addr: To address (optional)
            
        Returns:
            Complete MIMEMultipart message
        """
        # Create multipart message
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        
        if from_addr:
            msg['From'] = from_addr
        if to_addr:
            msg['To'] = to_addr
        
        # Convert placeholders to Gmail format
        gmail_text = text
        for img_id in images.keys():
            placeholder = f"{{{{{img_id}}}}}"
            # Use [image: ...] format for Gmail
            gmail_text = gmail_text.replace(placeholder, f"[image: {img_id}]")
        
        # Create text part
        text_part = MIMEText(gmail_text, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Attach images
        for img_id, (img_data, width, height, depth) in images.items():
            img = MIMEImage(img_data)
            img.add_header('Content-ID', f'<{img_id}>')
            img.add_header('Content-Disposition', 'inline', filename=f'{img_id}.png')
            msg.attach(img)
        
        return msg
    
    def build_html_email(self, text: str, images: Dict[str, tuple], 
                        subject: str = "LaTeX Email",
                        from_addr: Optional[str] = None,
                        to_addr: Optional[str] = None) -> MIMEMultipart:
        """Build a complete MIME email with embedded images.
        
        Args:
            text: Text with image placeholders
            images: Dict mapping placeholder IDs to (bytes, width, height, depth)
            subject: Email subject
            from_addr: From address (optional)
            to_addr: To address (optional)
            
        Returns:
            Complete MIMEMultipart message
        """
        # Create multipart message
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        
        if from_addr:
            msg['From'] = from_addr
        if to_addr:
            msg['To'] = to_addr
        
        # Convert text to HTML
        html_content = self._text_to_html(text, images)
        
        # Create HTML part
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Attach images
        for img_id, (img_data, width, height, depth) in images.items():
            img = MIMEImage(img_data)
            img.add_header('Content-ID', f'<{img_id}>')
            img.add_header('Content-Disposition', 'inline', filename=f'{img_id}.png')
            msg.attach(img)
        
        return msg
    
    def _text_to_html(self, text: str, images: Dict[str, tuple]) -> str:
        """Convert text with placeholders to HTML with embedded images.
        
        Args:
            text: Text with {{LATEX_IMG_N}} placeholders
            images: Dict of images (used to check which placeholders have images)
            
        Returns:
            HTML string
        """
        # Escape HTML special characters
        html_text = self._escape_html(text)
        
        # Convert newlines to <br>
        html_text = html_text.replace('\n', '<br>\n')
        
        # Replace image placeholders with img tags
        for img_id, (img_data, width, height, depth) in images.items():
            placeholder = f"{{{{{img_id}}}}}"
            # Mimic Gmail's internal format for better paste compatibility
            # Calculate vertical offset based on image height
            vertical_offset = -height * 0.2  # Approximate baseline adjustment
            img_tag = f'<img src="cid:{img_id}" width="{width}" height="{height}" style="display:inline;vertical-align:{vertical_offset:.3f}px" class="CToWUd" data-bit="iit" alt="LaTeX expression">'
            html_text = html_text.replace(placeholder, img_tag)
        
        # Wrap in basic HTML structure
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        img {{
            /* Styles are inline for Gmail compatibility */
        }}
    </style>
</head>
<body>
    {html_text}
</body>
</html>"""
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        
        for char, escape in replacements.items():
            text = text.replace(char, escape)
        
        return text
    
    def build_raw_mime(self, text: str, images: Dict[str, tuple],
                      subject: str = "LaTeX Email") -> str:
        """Build raw MIME string suitable for Gmail API.
        
        Args:
            text: Text with image placeholders
            images: Dict mapping placeholder IDs to (bytes, width, height, depth)
            subject: Email subject
            
        Returns:
            Base64-encoded MIME message string
        """
        msg = self.build_html_email(text, images, subject)
        
        # Convert to string
        mime_string = msg.as_string()
        
        # Base64 encode for Gmail API
        return base64.urlsafe_b64encode(mime_string.encode()).decode()
    
    def save_as_eml(self, text: str, images: Dict[str, tuple],
                    subject: str = "LaTeX Email", 
                    from_addr: str = "user@example.com",
                    to_addr: str = "recipient@example.com") -> str:
        """Save email as .eml file that can be opened in email clients.
        
        Returns:
            Raw MIME message string
        """
        msg = self.build_html_email(text, images, subject, from_addr, to_addr)
        return msg.as_string()
    
    def build_clipboard_html(self, text: str, images: Dict[str, tuple]) -> str:
        """Build HTML suitable for clipboard with inline base64 images.
        
        Args:
            text: Text with image placeholders
            images: Dict mapping placeholder IDs to (bytes, width, height, depth)
            
        Returns:
            HTML string with inline base64 images
        """
        # Start with escaped text
        html_text = self._escape_html(text)
        
        # Replace placeholders with inline base64 images
        for img_id, (img_data, width, height, depth) in images.items():
            placeholder = f"{{{{{img_id}}}}}"
            base64_data = base64.b64encode(img_data).decode()
            # Mimic Gmail's internal format
            vertical_offset = -height * 0.2
            img_tag = f'<img src="data:image/png;base64,{base64_data}" width="{width}" height="{height}" style="display:inline;vertical-align:{vertical_offset:.3f}px" class="CToWUd" data-bit="iit" alt="LaTeX expression">'
            html_text = html_text.replace(placeholder, img_tag)
        
        # Convert newlines to <br>
        html_text = html_text.replace('\n', '<br>')
        
        return html_text