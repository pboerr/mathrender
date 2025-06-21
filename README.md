# MathRender

Convert LaTeX mathematical expressions to images for web and email.

## Features

- Convert LaTeX expressions to HTML with embedded images
- **Secure email sending via SendGrid API (no password exposure)**
- SMTP support for Gmail, Outlook, and other providers
- Automatic browser preview for easy copying
- High-quality PNG rendering of mathematical expressions
- Simple command-line interface
- Support for both inline ($...$) and display ($$...$$) math

## Installation

### Prerequisites

You need a LaTeX distribution and dvipng installed on your system:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install texlive-latex-base texlive-latex-extra dvipng
```

**macOS:**
```bash
# Install MacTeX or BasicTeX
brew install --cask mactex
# OR for a smaller installation:
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install dvipng preview
```

**Windows:**
Install [MiKTeX](https://miktex.org/) which includes dvipng.

### Install mathrender

```bash
pip install mathrender
```

Or install from source:
```bash
git clone https://github.com/yourusername/mathrender.git
cd mathrender
pip install -e .
```

## Quick Start

### SendGrid Setup (Recommended - More Secure)

1. **Get a Free SendGrid Account:**
   - Sign up at https://sendgrid.com (free tier: 100 emails/day)
   - Go to Settings → API Keys → Create API Key
   - Copy your API key

2. **Set Environment Variable:**
   ```bash
   export SENDGRID_API_KEY="SG.xxxxxxxxxxxxxxxxxxxx"
   ```

3. **Send Your First Email:**
   ```bash
   mathrender 'The equation $E = mc^2$ is revolutionary!' --sendgrid --to recipient@example.com
   ```

That's it! No email passwords needed - just a secure API key.

### Basic Usage

Convert LaTeX expressions and preview in browser:
```bash
mathrender 'The integral $$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$ is beautiful.'
```

This automatically:
1. Converts LaTeX expressions to images
2. Creates an HTML file with embedded images
3. Opens it in your browser
4. You can then copy and paste into Gmail

### More Examples

**From a file:**
```bash
mathrender -f document.txt
```

**Save as PNG:**
```bash
mathrender 'Einstein showed that $E = mc^2$ revolutionized physics.' --png output.png
```

**From stdin:**
```bash
echo 'The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$.' | mathrender
```

**Generate MIME for email systems:**
```bash
mathrender -f document.txt --mime
```

**Save as .eml file (opens in email clients):**
```bash
mathrender 'The equation $E = mc^2$ is famous.' --eml output.eml
```

**Send email directly:**
```bash
# SendGrid (recommended - most secure)
export SENDGRID_API_KEY="SG.xxxxxxxxxxxxxxxxxxxx"
mathrender 'Math: $E = mc^2$' --sendgrid --to recipient@example.com

# Or pass API key directly
mathrender -f document.txt --sendgrid --to recipient@example.com \
    --sendgrid-api-key 'SG.xxxxxxxxxxxxxxxxxxxx'

# SMTP alternatives (Gmail, Outlook, etc.)
mathrender 'Content' --send --to recipient@example.com \
    --smtp-provider gmail --smtp-user you@gmail.com --smtp-pass 'app-password'
```

## Command Reference

### Basic Usage

```bash
mathrender [OPTIONS] [INPUT]
```

**Options:**
- `-f, --file PATH`: Read input from file
- `-o, --output PATH`: Save output to file (MIME format)
- `-p, --png PATH`: Save as PNG image file
- `--mime`: Output MIME content instead of opening HTML
- `--eml PATH`: Save as .eml file that opens in email clients
- `--dpi INTEGER`: Image resolution (default: 110)
- `--subject TEXT`: Email subject line
- `--from TEXT`: From email address
- `--to TEXT`: To email address (required for sending)
- `--raw`: Output raw MIME without base64 encoding

**Email Sending Options:**
- `--sendgrid`: Send via SendGrid API (recommended)
- `--sendgrid-api-key`: SendGrid API key (or use SENDGRID_API_KEY env var)
- `--send`: Send via SMTP
- `--smtp-provider`: Use preset for gmail/outlook/yahoo/office365
- `--smtp-host`: Custom SMTP server hostname
- `--smtp-port`: Custom SMTP server port
- `--smtp-user`: SMTP username (usually your email)
- `--smtp-pass`: SMTP password (use app passwords for Gmail/Outlook)

### Check Dependencies

Verify all dependencies are installed:
```bash
mathrender --check
```

## How It Works

1. **LaTeX Detection**: The tool finds LaTeX expressions in your text using common delimiters:
   - Inline math: `$...$` or `\(...\)`
   - Display math: `$$...$$` or `\[...\]`

2. **Image Generation**: Each expression is:
   - Compiled with LaTeX
   - Converted to PNG with dvipng
   - Optimized for email display

3. **HTML Output**: 
   - Creates HTML with embedded base64 images
   - Opens in your default browser
   - Ready to copy and paste

## Tips for Gmail

### Copy/Paste Method
1. The HTML preview opens automatically in your browser
2. Select all content (Ctrl+A or Cmd+A)
3. Copy (Ctrl+C or Cmd+C)
4. Paste into Gmail compose window
5. After pasting, you can resize images by clicking and dragging
6. The images are embedded, so recipients don't need to "load images"
7. Works with Gmail's confidential mode

**Note:** Gmail may strip some styling during paste operations, which can affect image alignment.

### EML File Method (Recommended for Perfect Formatting)
If you experience alignment issues with copy/paste, use the `.eml` file approach:

```bash
mathrender 'Your text with $LaTeX$ expressions' --eml email.eml
```

Then:
1. Double-click the `.eml` file to open it in your default email client
2. The email will open with all formatting preserved
3. Add recipients and send

This method preserves all styling and ensures perfect image alignment.

### Direct Email Sending (No Email Client Needed)

#### SendGrid API (Recommended - Most Secure)
No password exposure - just use an API key:

**Quick Setup:**
1. Sign up for free at https://sendgrid.com (100 emails/day free)
2. Create API key: Settings → API Keys → Create API Key
3. Set environment variable:
   ```bash
   export SENDGRID_API_KEY="SG.xxxxxxxxxxxxxxxxxxxx"
   ```
4. Send emails:
   ```bash
   mathrender 'Your $LaTeX$ content' --sendgrid --to recipient@example.com
   ```

**Why SendGrid?**
- No password exposure (API keys can be revoked anytime)
- Better deliverability
- Free tier is generous (100 emails/day)
- No 2FA or app passwords needed

#### SMTP Alternative (Gmail, Outlook, etc.)
If you prefer SMTP:
```bash
mathrender 'Content' --send --to recipient@example.com \
    --smtp-provider gmail --smtp-user you@gmail.com --smtp-pass 'app-password'
```

**Note:** SMTP requires app passwords for Gmail/Outlook, which is less secure than API keys.

## Troubleshooting

### "LaTeX compilation failed"
Make sure you have the required LaTeX packages:
```bash
sudo apt install texlive-latex-extra texlive-fonts-recommended
```

### "dvipng: command not found"
Install dvipng:
```bash
sudo apt install dvipng
```

### Images appear too large/small
Adjust the DPI setting:
```bash
mathrender "your text" --dpi 150
```

### Browser doesn't open automatically
The HTML file is saved to a temporary location. Look for the path in the output:
```
✓ HTML opened in browser: /tmp/tmpXXXXXX.html
```
You can manually open this file in your browser.

## Development

### Setup
```bash
git clone https://github.com/yourusername/mathrender.git
cd mathrender
pip install -e .
```

### Running Tests
```bash
pytest
```

## License

MIT License - see LICENSE file for details.