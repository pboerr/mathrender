"""Command-line interface for mathrender."""

import sys
import click
import subprocess
import tempfile
import os
import webbrowser
from pathlib import Path
from .converter import LatexToEmailConverter
from .mime_builder import MimeEmailBuilder
from .simple_gmail import convert_to_gmail_format


@click.command()
@click.version_option()
@click.argument('input', required=False)
@click.option('-f', '--file', type=click.Path(exists=True), 
              help='Input file containing LaTeX text')
@click.option('-o', '--output', type=click.Path(),
              help='Output file for MIME content')
@click.option('--dpi', type=int, default=300,
              help='DPI for generated images (default: 300)')
@click.option('--subject', default='LaTeX Email',
              help='Email subject line')
@click.option('--from', 'from_addr', help='From email address')
@click.option('--to', 'to_addr', help='To email address')
@click.option('--png', '-p', type=click.Path(),
              help='Save as PNG image file')
@click.option('--mime', is_flag=True,
              help='Output MIME content instead of opening HTML')
@click.option('--raw', '-r', is_flag=True,
              help='Output raw MIME without base64 encoding')
@click.option('--full-latex', is_flag=True,
              help='Treat entire input as LaTeX code (for complete LaTeX documents)')
@click.option('--check', is_flag=True,
              help='Check if all required dependencies are installed')
@click.option('--gmail', is_flag=True,
              help='Convert to Gmail format [image: ...]')
def main(input, file, output, dpi, subject, from_addr, to_addr, png, mime, raw, full_latex, check, gmail):
    """Convert LaTeX mathematical expressions to images.
    
    By default, generates HTML and opens it in your browser for easy copying to Gmail.
    
    Examples:
    
        # Direct input (default: opens HTML in browser)
        mathrender 'The equation $E = mc^2$ is famous.'
        
        # From file
        mathrender -f document.txt
        
        # Save as PNG
        mathrender 'The formula $x^2$' --png output.png
        
        # Check dependencies
        mathrender --check
        
        # Gmail format
        mathrender --gmail '$x^2 + y^2 = z^2$'
    """
    # Handle special commands
    if check:
        check_dependencies()
        return
    
    # Get input text
    if file:
        input_text = Path(file).read_text(encoding='utf-8')
    elif input:
        input_text = input
    else:
        # Read from stdin
        input_text = sys.stdin.read()
    
    if not input_text.strip():
        click.echo("Error: No input provided", err=True)
        click.echo("\nUsage: mathrender 'Your text with $LaTeX$ expressions'")
        click.echo("Or: mathrender -f document.txt")
        sys.exit(1)
    
    # Handle Gmail format
    if gmail:
        gmail_text = convert_to_gmail_format(input_text)
        click.echo(gmail_text)
        return
    
    # Initialize converter and builder
    converter = LatexToEmailConverter(dpi=dpi)
    builder = MimeEmailBuilder()
    
    try:
        # Process LaTeX
        if full_latex:
            # Treat entire input as LaTeX
            try:
                image_bytes = converter.latex_to_image(input_text, is_display=True, is_raw=True)
                processed_text = "{LATEX_IMG_0}"
                images = {"LATEX_IMG_0": image_bytes}
            except Exception as e:
                click.echo(f"Error converting LaTeX: {e}", err=True)
                sys.exit(1)
        else:
            processed_text, images = converter.process_text(input_text)
        
        if png:
            # Save as PNG file
            if images:
                # Get the first (or only) image
                img_key = list(images.keys())[0]
                img_bytes = images[img_key]
                
                Path(png).write_bytes(img_bytes)
                click.echo(f"Image saved to {png}")
            else:
                click.echo("No LaTeX expressions found in the input.")
                sys.exit(1)
        elif mime or output:
            # Build MIME email
            if raw:
                # Build complete MIME message
                msg = builder.build_html_email(processed_text, images, subject,
                                             from_addr, to_addr)
                mime_content = msg.as_string()
            else:
                # Build base64-encoded MIME for Gmail API
                mime_content = builder.build_raw_mime(processed_text, images, subject)
            
            # Output
            if output:
                Path(output).write_text(mime_content, encoding='utf-8')
                click.echo(f"MIME content written to {output}")
            else:
                click.echo(mime_content)
        else:
            # Default: Generate HTML and open in browser
            html_content = builder.build_clipboard_html(processed_text, images)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MathRender Output</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .content {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .instructions {{
            background-color: #e3f2fd;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 1px solid #90caf9;
        }}
        img {{
            vertical-align: middle;
            margin: 0 4px;
        }}
    </style>
</head>
<body>
    <div class="instructions">
        <h3>📋 Copy to Gmail:</h3>
        <ol>
            <li>Select all content below (Ctrl+A or Cmd+A)</li>
            <li>Copy (Ctrl+C or Cmd+C)</li>
            <li>Paste into Gmail compose window (Ctrl+V or Cmd+V)</li>
        </ol>
    </div>
    <div class="content">
        <div dir="ltr">{html_content}</div>
    </div>
</body>
</html>"""
                f.write(full_html)
                temp_html_path = f.name
            
            # Open in browser
            webbrowser.open(f'file://{os.path.abspath(temp_html_path)}')
            click.echo(f"✓ HTML opened in browser: {temp_html_path}")
            click.echo("\nThe content is ready to copy and paste into Gmail.")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are installed."""
    dependencies = {
        'latex': ('--version', 'LaTeX distribution'),
        'dvipng': ('--version', 'dvipng (LaTeX to PNG converter)'),
    }
    
    all_good = True
    
    for cmd, (version_flag, description) in dependencies.items():
        try:
            proc = subprocess.run([cmd, version_flag], 
                                 capture_output=True, 
                                 timeout=5,
                                 text=True)
            if proc.returncode == 0:
                click.echo(f"✓ {description}: Found")
            else:
                click.echo(f"✗ {description}: Error", err=True)
                all_good = False
        except FileNotFoundError:
            click.echo(f"✗ {description}: Not found", err=True)
            all_good = False
        except subprocess.TimeoutExpired:
            click.echo(f"? {description}: Check timed out", err=True)
    
    if all_good:
        click.echo("\n✓ All dependencies are installed!")
    else:
        click.echo("\n✗ Some dependencies are missing. Please install them.", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()