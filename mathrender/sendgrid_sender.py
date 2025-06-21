"""SendGrid email sender for mathrender."""

import os
import json
import base64
from typing import Dict, Optional
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.error


class SendGridSender:
    """Send emails via SendGrid API."""
    
    API_URL = "https://api.sendgrid.com/v3/mail/send"
    
    def __init__(self, api_key: str = None):
        """Initialize SendGrid sender.
        
        Args:
            api_key: SendGrid API key (or from SENDGRID_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            raise ValueError("SendGrid API key required. Set SENDGRID_API_KEY environment variable.")
    
    def send_email(self, msg: MIMEMultipart, to_addr: str = None) -> bool:
        """Send email via SendGrid API.
        
        Args:
            msg: Complete MIME message to send
            to_addr: Override recipient address
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Extract email components from MIME message
        from_addr = msg['From'] or 'noreply@mathrender.com'
        to_addr = to_addr or msg['To']
        subject = msg['Subject'] or 'LaTeX Email'
        
        # Extract HTML content and images
        html_content = None
        images = []
        
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                html_content = part.get_payload(decode=True).decode('utf-8')
            elif part.get_content_type().startswith('image/'):
                content_id = part.get('Content-ID', '').strip('<>')
                if content_id:
                    images.append({
                        'content': base64.b64encode(part.get_payload(decode=True)).decode(),
                        'type': part.get_content_type(),
                        'filename': f"{content_id}.png",
                        'disposition': 'inline',
                        'content_id': content_id
                    })
        
        # Build SendGrid API request
        data = {
            'personalizations': [{
                'to': [{'email': to_addr}]
            }],
            'from': {'email': from_addr},
            'subject': subject,
            'content': [{
                'type': 'text/html',
                'value': html_content or '<p>No content</p>'
            }]
        }
        
        # Add inline images as attachments
        if images:
            data['attachments'] = images
        
        # Send request
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            request = urllib.request.Request(
                self.API_URL,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(request) as response:
                return response.status == 202  # SendGrid returns 202 for success
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"SendGrid API error: {e.code} - {error_body}")
            return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False