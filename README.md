# MathRender

Convert LaTeX mathematical expressions to images for web and email.

## Features

- Convert LaTeX expressions to HTML with embedded images
- Automatic browser preview for easy copying to Gmail
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
- `--dpi INTEGER`: Image resolution (default: 300)
- `--subject TEXT`: Email subject line (for MIME output)
- `--from TEXT`: From email address (for MIME output)
- `--to TEXT`: To email address (for MIME output)
- `--raw`: Output raw MIME without base64 encoding

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

1. The HTML preview opens automatically in your browser
2. Select all content (Ctrl+A or Cmd+A)
3. Copy (Ctrl+C or Cmd+C)
4. Paste into Gmail compose window
5. After pasting, you can resize images by clicking and dragging
6. The images are embedded, so recipients don't need to "load images"
7. Works with Gmail's confidential mode

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