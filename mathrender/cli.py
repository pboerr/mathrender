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
from .smtp_sender import SmtpSender
from .sendgrid_sender import SendGridSender


@click.command()
@click.version_option()
@click.argument('input', required=False)
@click.option('-f', '--file', type=click.Path(exists=True), 
              help='Input file containing LaTeX text')
@click.option('-o', '--output', type=click.Path(),
              help='Output file for MIME content')
@click.option('--dpi', type=int, default=110,
              help='DPI for generated images (default: 110)')
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
@click.option('--eml', type=click.Path(),
              help='Save as .eml file that opens in email clients')
@click.option('--full-latex', is_flag=True,
              help='Treat entire input as LaTeX code (for complete LaTeX documents)')
@click.option('--check', is_flag=True,
              help='Check if all required dependencies are installed')
@click.option('--gmail', is_flag=True,
              help='Convert to Gmail format [image: ...]')
@click.option('--send', is_flag=True,
              help='Send email via SMTP or SendGrid')
@click.option('--sendgrid', is_flag=True,
              help='Use SendGrid API instead of SMTP (recommended)')
@click.option('--sendgrid-api-key', help='SendGrid API key (or use SENDGRID_API_KEY env var)')
@click.option('--smtp-host', help='SMTP server hostname')
@click.option('--smtp-port', type=int, help='SMTP server port')
@click.option('--smtp-user', help='SMTP username (usually your email)')
@click.option('--smtp-pass', help='SMTP password')
@click.option('--smtp-provider', type=click.Choice(['gmail', 'outlook', 'yahoo', 'office365']),
              help='Use preset SMTP settings for provider')
def main(input, file, output, dpi, subject, from_addr, to_addr, png, mime, raw, eml, 
         full_latex, check, gmail, send, sendgrid, sendgrid_api_key, smtp_host, smtp_port, 
         smtp_user, smtp_pass, smtp_provider):
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
        
        # Send email via SendGrid (recommended - more secure)
        export SENDGRID_API_KEY='your-api-key'
        mathrender -f document.txt --sendgrid --to recipient@example.com
        
        # Or via SMTP (Gmail)
        mathrender -f document.txt --send --to recipient@example.com \\
            --smtp-provider gmail --smtp-user you@gmail.com --smtp-pass 'app-password'
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
                image_data = converter.latex_to_image(input_text, is_display=True, is_raw=True)
                processed_text = "{LATEX_IMG_0}"
                images = {"LATEX_IMG_0": image_data}
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
                img_bytes, width, height, depth = images[img_key]
                
                Path(png).write_bytes(img_bytes)
                click.echo(f"Image saved to {png}")
            else:
                click.echo("No LaTeX expressions found in the input.")
                sys.exit(1)
        elif eml:
            # Save as .eml file
            eml_content = builder.save_as_eml(processed_text, images, subject, 
                                            from_addr or "sender@example.com",
                                            to_addr or "recipient@example.com")
            Path(eml).write_text(eml_content, encoding='utf-8')
            click.echo(f"✓ Email saved to {eml}")
            click.echo("Double-click to open in your default email client")
        elif send or sendgrid:
            # Send email
            if not to_addr:
                click.echo("Error: --to is required when sending email", err=True)
                sys.exit(1)
                
            # Build email message
            msg = builder.build_html_email(processed_text, images, subject,
                                         from_addr or "noreply@mathrender.com", to_addr)
            
            try:
                if sendgrid:
                    # Use SendGrid API
                    sender = SendGridSender(sendgrid_api_key)
                    if sender.send_email(msg):
                        click.echo(f"✓ Email sent successfully via SendGrid to {to_addr}")
                    else:
                        click.echo("✗ Failed to send email via SendGrid", err=True)
                        sys.exit(1)
                else:
                    # Use SMTP
                    if smtp_provider and smtp_user and smtp_pass:
                        # Use provider presets
                        sender = SmtpSender.from_provider(smtp_provider, smtp_user, smtp_pass)
                    elif smtp_user and smtp_pass and not smtp_host:
                        # Default to Gmail if only user/pass provided
                        sender = SmtpSender.from_provider('gmail', smtp_user, smtp_pass)
                    else:
                        # Use custom SMTP settings
                        sender = SmtpSender(smtp_host, smtp_port, smtp_user, smtp_pass)
                    
                    # Send email
                    if sender.send_email(msg):
                        click.echo(f"✓ Email sent successfully via SMTP to {to_addr}")
                    else:
                        click.echo("✗ Failed to send email", err=True)
                        sys.exit(1)
                    
            except ValueError as e:
                click.echo(f"Error: {e}", err=True)
                if sendgrid:
                    click.echo("\nTo use SendGrid:")
                    click.echo("1. Sign up at https://sendgrid.com (free)")
                    click.echo("2. Get your API key from Settings > API Keys")
                    click.echo("3. Set environment variable: export SENDGRID_API_KEY='your-key'")
                    click.echo("4. Or use: --sendgrid-api-key 'your-key'")
                else:
                    click.echo("\nTo send emails via SMTP, provide credentials either:")
                    click.echo("1. Via environment variables: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS")
                    click.echo("2. Via command options: --smtp-host, --smtp-port, --smtp-user, --smtp-pass")
                    click.echo("3. Via provider preset: --smtp-provider gmail --smtp-user you@gmail.com --smtp-pass 'app-password'")
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
        <div>{html_content}</div>
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