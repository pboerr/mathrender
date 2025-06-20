"""Tests for the LaTeX to image converter."""

import pytest
from mathrender.converter import LatexToEmailConverter


class TestLatexToEmailConverter:
    """Test the LaTeX converter functionality."""
    
    def test_extract_inline_math(self):
        """Test extraction of inline math expressions."""
        converter = LatexToEmailConverter()
        text = "Here is $x^2$ and also $y = mx + b$ inline."
        expressions = converter.extract_latex_expressions(text)
        
        assert len(expressions) == 2
        assert expressions[0][1] == "x^2"
        assert expressions[0][2] == False  # is_display
        assert expressions[1][1] == "y = mx + b"
        assert expressions[1][2] == False
    
    def test_extract_display_math(self):
        """Test extraction of display math expressions."""
        converter = LatexToEmailConverter()
        text = "Display math: $$\\int_0^1 x^2 dx = \\frac{1}{3}$$ and more."
        expressions = converter.extract_latex_expressions(text)
        
        assert len(expressions) == 1
        assert expressions[0][1] == "\\int_0^1 x^2 dx = \\frac{1}{3}"
        assert expressions[0][2] == True  # is_display
    
    def test_extract_mixed_delimiters(self):
        """Test extraction with mixed delimiter types."""
        converter = LatexToEmailConverter()
        text = "Mix: $a + b$, \\(c - d\\), $$e \\times f$$, and \\[g \\div h\\]"
        expressions = converter.extract_latex_expressions(text)
        
        assert len(expressions) == 4
        assert expressions[0][1] == "a + b"
        assert expressions[1][1] == "c - d"
        assert expressions[2][1] == "e \\times f"
        assert expressions[3][1] == "g \\div h"
    
    def test_no_latex_expressions(self):
        """Test text without LaTeX expressions."""
        converter = LatexToEmailConverter()
        text = "This is plain text without any math."
        expressions = converter.extract_latex_expressions(text)
        
        assert len(expressions) == 0
    
    def test_latex_to_image_simple(self):
        """Test simple LaTeX to image conversion."""
        converter = LatexToEmailConverter()
        
        # Test simple expression
        try:
            image_bytes = converter.latex_to_image("x^2")
            assert isinstance(image_bytes, bytes)
            assert len(image_bytes) > 0
            # PNG file signature
            assert image_bytes[:4] == bytes([137, 80, 78, 71])
        except RuntimeError as e:
            if "LaTeX compilation failed" in str(e) or "dvipng" in str(e):
                pytest.skip("LaTeX or dvipng not available")
            raise
    
    def test_latex_to_image_complex(self):
        """Test complex LaTeX to image conversion."""
        converter = LatexToEmailConverter()
        
        # Test complex expression
        try:
            image_bytes = converter.latex_to_image("\\frac{\\partial f}{\\partial x} = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}")
            assert isinstance(image_bytes, bytes)
            assert len(image_bytes) > 0
            assert image_bytes[:4] == bytes([137, 80, 78, 71])
        except RuntimeError as e:
            if "LaTeX compilation failed" in str(e) or "dvipng" in str(e):
                pytest.skip("LaTeX or dvipng not available")
            raise
    
    def test_process_text_simple(self):
        """Test processing text with LaTeX expressions."""
        converter = LatexToEmailConverter()
        
        text = "The quadratic formula is $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$."
        
        try:
            processed_text, images = converter.process_text(text)
            
            # Check that placeholder was inserted
            assert "{{LATEX_IMG_0}}" in processed_text
            assert "$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$" not in processed_text
            
            # Check that image was generated
            assert "LATEX_IMG_0" in images
            assert isinstance(images["LATEX_IMG_0"], bytes)
            assert images["LATEX_IMG_0"][:4] == bytes([137, 80, 78, 71])
        except RuntimeError as e:
            if "LaTeX compilation failed" in str(e) or "dvipng" in str(e):
                pytest.skip("LaTeX or dvipng not available")
            raise
    
    def test_process_text_multiple(self):
        """Test processing text with multiple LaTeX expressions."""
        converter = LatexToEmailConverter()
        
        text = "First: $a^2$, then $$b^3$$, finally $c^4$."
        
        try:
            processed_text, images = converter.process_text(text)
            
            # Check placeholders
            assert "{{LATEX_IMG_0}}" in processed_text
            assert "{{LATEX_IMG_1}}" in processed_text
            assert "{{LATEX_IMG_2}}" in processed_text
            
            # Check all images generated
            assert len(images) == 3
            for i in range(3):
                assert f"LATEX_IMG_{i}" in images
        except RuntimeError as e:
            if "LaTeX compilation failed" in str(e) or "dvipng" in str(e):
                pytest.skip("LaTeX or dvipng not available")
            raise
    
    def test_invalid_latex(self):
        """Test handling of invalid LaTeX."""
        converter = LatexToEmailConverter()
        
        # This should fail compilation
        with pytest.raises(RuntimeError, match="LaTeX compilation failed"):
            converter.latex_to_image("\\undefined_command")
    
    def test_overlapping_expressions(self):
        """Test that overlapping expressions are handled correctly."""
        converter = LatexToEmailConverter()
        
        # Dollar signs that might confuse the parser
        text = "Price is $10 and $20, not LaTeX."
        expressions = converter.extract_latex_expressions(text)
        
        # Should extract as one expression (though not valid LaTeX)
        assert len(expressions) == 1
        assert expressions[0][1] == "10 and $20, not LaTeX."