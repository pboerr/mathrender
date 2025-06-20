"""Simple Gmail LaTeX converter based on common patterns."""

import re


def convert_to_gmail_format(text: str) -> str:
    """Convert common LaTeX patterns to Gmail's [image: ...] format."""
    
    # List of patterns to convert
    # Each tuple is (pattern, group_to_capture)
    patterns = [
        # Complex expressions with bigoplus, subscripts, etc.
        (r'((?:[A-Za-z0-9]+\^{[^}]+}\s*=\s*)?\\bigoplus_{[^}]+}\s*[A-Za-z]+)', 1),
        # mathbb{Z}^n and similar
        (r'(\\mathbb{[A-Z]}(?:\^[A-Za-z0-9]+|\^{[^}]+})?)', 1),
        # Simple expressions like A^n, A^{(I)}
        (r'([A-Za-z]+\^{[^}]+})', 1),
        # Set notation with langle/rangle
        (r'(\\langle\s*[^\\]+\s*\\rangle)', 1),
        # Expressions with = 
        (r'([A-Za-z0-9\s]+\s*=\s*[A-Za-z0-9\s]+)', 1),
        # Set membership and operations
        (r'(\\{[^}]*\\})', 1),
        # Fraction expressions
        (r'(\\frac{[^}]+}{[^}]+})', 1),
        # Math operators like \cong, \times
        (r'(\\(?:cong|times|div|cdot|oplus|otimes))', 1),
        # Expressions like am = 0
        (r'([a-zA-Z]+[a-zA-Z0-9]*\s*=\s*\d+)', 1),
        # Expressions with cdot
        (r'(\d+\s*\\cdot\s*\d+)', 1),
        # Complex expressions with parentheses
        (r'(\([^)]+\))', 1) if '\\' in text else (None, None),
    ]
    
    # Track what's been converted to avoid double conversion
    converted_ranges = []
    result = text
    
    for pattern, group in patterns:
        if pattern is None:
            continue
            
        for match in re.finditer(pattern, text):
            start, end = match.span(group)
            
            # Check if this range overlaps with already converted text
            overlaps = any(start < conv_end and end > conv_start 
                          for conv_start, conv_end in converted_ranges)
            
            if not overlaps:
                latex_expr = match.group(group)
                # Don't convert if it's already in [image: ...] format
                if not (start > 7 and text[start-8:start] == '[image: '):
                    # Replace in result
                    result = result.replace(latex_expr, f'[image: {latex_expr}]', 1)
                    converted_ranges.append((start, end))
    
    return result