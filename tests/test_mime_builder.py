"""Tests for the MIME email builder."""

import pytest
import base64
from email import message_from_string
from mathrender.mime_builder import MimeEmailBuilder


class TestMimeEmailBuilder:
    """Test the MIME email builder functionality."""
    
    def test_escape_html(self):
        """Test HTML escaping."""
        builder = MimeEmailBuilder()
        
        text = 'Test <script>alert("XSS")</script> & more'
        escaped = builder._escape_html(text)
        
        assert '<' not in escaped
        assert '>' not in escaped
        assert '&' not in escaped
        assert escaped == 'Test &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt; &amp; more'
    
    def test_text_to_html_basic(self):
        """Test basic text to HTML conversion."""
        builder = MimeEmailBuilder()
        
        text = "Line 1\\nLine 2"
        html = builder._text_to_html(text, {})
        
        assert "<br>" in html
        assert "Line 1<br>" in html
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
    
    def test_text_to_html_with_images(self):
        """Test HTML generation with image placeholders."""
        builder = MimeEmailBuilder()
        
        text = "Math: {{LATEX_IMG_0}} and {{LATEX_IMG_1}}"
        images = {"LATEX_IMG_0": b"fake_image_1", "LATEX_IMG_1": b"fake_image_2"}
        
        html = builder._text_to_html(text, images)
        
        assert 'src="cid:LATEX_IMG_0"' in html
        assert 'src="cid:LATEX_IMG_1"' in html
        assert "{{LATEX_IMG_0}}" not in html
        assert "{{LATEX_IMG_1}}" not in html
    
    def test_build_html_email(self):
        """Test building complete MIME email."""
        builder = MimeEmailBuilder()
        
        text = "Test with image: {{LATEX_IMG_0}}"
        images = {"LATEX_IMG_0": bytes([137, 80, 78, 71, 13, 10, 26, 10])}  # Minimal PNG header
        
        msg = builder.build_html_email(
            text, images,
            subject="Test Email",
            from_addr="sender@example.com",
            to_addr="recipient@example.com"
        )
        
        # Check headers
        assert msg['Subject'] == "Test Email"
        assert msg['From'] == "sender@example.com"
        assert msg['To'] == "recipient@example.com"
        assert msg['Date'] is not None
        
        # Check multipart structure
        assert msg.is_multipart()
        assert msg.get_content_type() == 'multipart/related'
        
        # Check parts
        parts = list(msg.walk())
        assert len(parts) == 3  # Root, HTML part, Image part
        
        # Check HTML part
        html_part = parts[1]
        assert html_part.get_content_type() == 'text/html'
        
        # Check image part
        img_part = parts[2]
        assert img_part.get_content_type() == 'image/png'
        assert img_part['Content-ID'] == '<LATEX_IMG_0>'
    
    def test_build_raw_mime(self):
        """Test building base64-encoded MIME for Gmail API."""
        builder = MimeEmailBuilder()
        
        text = "Simple test"
        images = {}
        
        raw_mime = builder.build_raw_mime(text, images, subject="Test")
        
        # Should be base64 encoded
        assert isinstance(raw_mime, str)
        
        # Decode and verify
        decoded = base64.urlsafe_b64decode(raw_mime).decode()
        assert "Subject: Test" in decoded
        assert "Simple test" in decoded
    
    def test_build_clipboard_html(self):
        """Test building HTML for clipboard with inline images."""
        builder = MimeEmailBuilder()
        
        text = "Math: {{LATEX_IMG_0}}"
        images = {"LATEX_IMG_0": bytes([137, 80, 78, 71, 13, 10, 26, 10])}
        
        html = builder.build_clipboard_html(text, images)
        
        # Should have data URI
        assert 'src="data:image/png;base64,' in html
        assert "{{LATEX_IMG_0}}" not in html
        
        # Should have base64 encoded image
        expected_b64 = base64.b64encode(bytes([137, 80, 78, 71, 13, 10, 26, 10])).decode()
        assert expected_b64 in html
    
    def test_multiple_images_order(self):
        """Test that multiple images are handled in correct order."""
        builder = MimeEmailBuilder()
        
        text = "First {{LATEX_IMG_0}}, second {{LATEX_IMG_1}}, third {{LATEX_IMG_2}}"
        images = {
            "LATEX_IMG_0": b"img0",
            "LATEX_IMG_1": b"img1",
            "LATEX_IMG_2": b"img2"
        }
        
        msg = builder.build_html_email(text, images)
        
        # Get all image parts
        img_parts = [p for p in msg.walk() if p.get_content_type() == 'image/png']
        assert len(img_parts) == 3
        
        # Check each has correct Content-ID
        content_ids = [p['Content-ID'] for p in img_parts]
        assert '<LATEX_IMG_0>' in content_ids
        assert '<LATEX_IMG_1>' in content_ids
        assert '<LATEX_IMG_2>' in content_ids
    
    def test_newline_handling(self):
        """Test proper newline handling in HTML."""
        builder = MimeEmailBuilder()
        
        text = "Line 1\\nLine 2\\n\\nParagraph 2"
        html = builder._text_to_html(text, {})
        
        # Check newlines converted to <br>
        assert "Line 1<br>" in html
        assert "Line 2<br>" in html
        assert "<br>\\nParagraph 2" in html