"""SMTP email sender for mathrender."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
import os


class SmtpSender:
    """Send emails via SMTP."""
    
    # Common SMTP servers
    SMTP_SERVERS = {
        'gmail': ('smtp.gmail.com', 587, True),
        'outlook': ('smtp-mail.outlook.com', 587, True),
        'yahoo': ('smtp.mail.yahoo.com', 587, True),
        'aol': ('smtp.aol.com', 587, True),
        'office365': ('smtp.office365.com', 587, True),
    }
    
    def __init__(self, smtp_host: str = None, smtp_port: int = None, 
                 smtp_user: str = None, smtp_pass: str = None,
                 use_tls: bool = True):
        """Initialize SMTP sender.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username (usually email address)
            smtp_pass: SMTP password
            use_tls: Whether to use TLS encryption
        """
        # Default to Gmail if no host specified
        self.smtp_host = smtp_host or os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.environ.get('SMTP_USER')
        self.smtp_pass = smtp_pass or os.environ.get('SMTP_PASS')
        self.use_tls = use_tls
        
    def send_email(self, msg: MIMEMultipart, to_addr: str = None) -> bool:
        """Send email via SMTP.
        
        Args:
            msg: Complete MIME message to send
            to_addr: Override recipient address
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_pass]):
            raise ValueError("SMTP configuration incomplete. Set SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASS")
        
        # Override recipient if provided
        if to_addr:
            msg['To'] = to_addr
            
        # Ensure From address is set
        if not msg['From']:
            msg['From'] = self.smtp_user
            
        try:
            # Create SMTP connection
            if self.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                
            # Login and send
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
            
    @classmethod
    def from_provider(cls, provider: str, username: str, password: str):
        """Create SmtpSender for a known provider.
        
        Args:
            provider: Provider name (gmail, outlook, etc.)
            username: Email username
            password: Email password
            
        Returns:
            SmtpSender instance
        """
        if provider.lower() not in cls.SMTP_SERVERS:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {', '.join(cls.SMTP_SERVERS.keys())}")
            
        host, port, use_tls = cls.SMTP_SERVERS[provider.lower()]
        return cls(smtp_host=host, smtp_port=port, smtp_user=username, 
                  smtp_pass=password, use_tls=use_tls)