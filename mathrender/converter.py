"""LaTeX to image converter for email compatibility."""

import os
import re
import subprocess
import tempfile
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io


class LatexToEmailConverter:
    """Convert LaTeX expressions to images embedded in HTML for email."""
    
    def __init__(self, dpi: int = 300):
        """Initialize converter with specified DPI for image generation.
        
        Args:
            dpi: Dots per inch for generated images (default: 300)
        """
        self.dpi = dpi
        self.latex_template = r"""
\documentclass[preview,border=1pt]{{standalone}}
\usepackage[usenames]{{color}}
\usepackage{{amsmath}}
\usepackage{{amsfonts}}
\usepackage{{amssymb}}
\usepackage{{mathtools}}
\usepackage{{enumerate}}
\usepackage{{amsthm}}
% Define theorem environments
\newtheorem{{lem}}{{Lemma}}
\newtheorem{{thm}}{{Theorem}}
\newtheorem{{cor}}{{Corollary}}
\newtheorem{{prop}}{{Proposition}}
% Common custom commands
\newcommand{{\R}}{{\mathbb{{R}}}}
\newcommand{{\N}}{{\mathbb{{N}}}}
\newcommand{{\Z}}{{\mathbb{{Z}}}}
\newcommand{{\Q}}{{\mathbb{{Q}}}}
\newcommand{{\C}}{{\mathbb{{C}}}}
\pagestyle{{empty}}
\begin{{document}}
{}
\end{{document}}
"""
    
    def extract_latex_expressions(self, text: str) -> List[Tuple[str, str, bool]]:
        """Extract LaTeX expressions from text.
        
        Returns list of tuples: (full_match, latex_code, is_display)
        """
        expressions = []
        
        # Display math: $$...$$ or \[...\]
        display_patterns = [
            (r'\$\$(.*?)\$\$', True),
            (r'\\\[(.*?)\\\]', True)
        ]
        
        # Inline math: $...$ or \(...\)
        inline_patterns = [
            (r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', False),
            (r'\\\((.*?)\\\)', False)
        ]
        
        # Process all patterns
        all_patterns = display_patterns + inline_patterns
        
        # Find all matches with their positions
        matches = []
        for pattern, is_display in all_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                matches.append((match.start(), match.end(), match.group(0), match.group(1), is_display))
        
        # Sort by position and remove overlaps
        matches.sort(key=lambda x: x[0])
        
        last_end = -1
        for start, end, full_match, latex_code, is_display in matches:
            if start >= last_end:
                expressions.append((full_match, latex_code.strip(), is_display))
                last_end = end
        
        return expressions
    
    def latex_to_image(self, latex_code: str, is_display: bool = False, is_raw: bool = False) -> bytes:
        """Convert LaTeX code to PNG image bytes.
        
        Args:
            latex_code: LaTeX mathematical expression or raw LaTeX content
            is_display: Whether this is display math (centered) or inline
            is_raw: Whether the latex_code is raw LaTeX (no $ wrapping needed)
            
        Returns:
            PNG image as bytes
        """
        # If raw LaTeX, use as-is, otherwise wrap in $ or $$
        if is_raw:
            latex_content = latex_code
        elif is_display:
            latex_content = f"$${latex_code}$$"
        else:
            latex_content = f"${latex_code}$"
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write LaTeX file
            tex_file = os.path.join(tmpdir, "formula.tex")
            with open(tex_file, 'w') as f:
                # Use format instead of % to avoid issues with % in comments
                f.write(self.latex_template.format(latex_content))
            
            # Compile LaTeX to DVI
            try:
                subprocess.run(
                    ['latex', '-interaction=nonstopmode', '-output-directory', tmpdir, tex_file],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                print(f"LaTeX stderr: {e.stderr}")
                print(f"LaTeX stdout: {e.stdout}")
                raise RuntimeError(f"LaTeX compilation failed: {e.stderr}")
            
            # Convert DVI to PNG
            dvi_file = os.path.join(tmpdir, "formula.dvi")
            png_file = os.path.join(tmpdir, "formula.png")
            
            try:
                subprocess.run(
                    ['dvipng', '-D', str(self.dpi), '-T', 'tight', '-bg', 'Transparent', 
                     '-o', png_file, dvi_file],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"dvipng conversion failed: {e.stderr}")
            
            # Read and optimize PNG
            with Image.open(png_file) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Save optimized PNG to bytes
                output = io.BytesIO()
                img.save(output, format='PNG', optimize=True)
                return output.getvalue()
    
    def process_text(self, text: str) -> Tuple[str, Dict[str, bytes]]:
        """Process text containing LaTeX expressions.
        
        Args:
            text: Input text with LaTeX expressions
            
        Returns:
            Tuple of (processed_text, images_dict)
            - processed_text: Text with LaTeX replaced by placeholders
            - images_dict: Dict mapping placeholder IDs to PNG bytes
        """
        expressions = self.extract_latex_expressions(text)
        
        if not expressions:
            return text, {}
        
        processed_text = text
        images = {}
        
        # Process expressions in reverse order to maintain positions
        for i, (full_match, latex_code, is_display) in enumerate(reversed(expressions)):
            placeholder = f"{{{{LATEX_IMG_{len(expressions) - i - 1}}}}}"
            
            try:
                # Generate image
                image_bytes = self.latex_to_image(latex_code, is_display)
                images[f"LATEX_IMG_{len(expressions) - i - 1}"] = image_bytes
                
                # Replace in text
                processed_text = processed_text.replace(full_match, placeholder, 1)
            except Exception as e:
                # On error, leave the original LaTeX in place
                print(f"Warning: Failed to convert LaTeX: {latex_code}")
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
        
        return processed_text, images
    
    def process_file(self, file_path: str) -> Tuple[str, Dict[str, bytes]]:
        """Process a file containing LaTeX expressions.
        
        Args:
            file_path: Path to input file
            
        Returns:
            Same as process_text()
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.process_text(text)