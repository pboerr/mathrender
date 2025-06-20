"""Create rich clipboard content that Gmail recognizes."""

import subprocess
import tempfile
import platform
from typing import Dict, List, Tuple
import base64


def create_gmail_compatible_html(text: str, latex_expressions: List[Tuple[str, str, bool]], 
                                images: Dict[str, bytes]) -> str:
    """Create HTML that Gmail will recognize when pasted.
    
    This mimics the format Gmail uses internally.
    """
    html_parts = []
    last_pos = 0
    
    # Build HTML with inline images
    for i, (full_match, latex_code, is_display) in enumerate(latex_expressions):
        # Find position of this expression in text
        pos = text.find(full_match, last_pos)
        if pos == -1:
            continue
            
        # Add text before the expression
        text_before = text[last_pos:pos]
        html_parts.append(text_before.replace('\n', '<br>'))
        
        # Add the image
        img_id = f"latex_{i}"
        if img_id in images:
            img_data = base64.b64encode(images[img_id]).decode()
            # Gmail-style image tag
            html_parts.append(
                f'<img src="data:image/png;base64,{img_data}" '
                f'alt="{latex_code}" '
                f'style="vertical-align: middle; display: {"block" if is_display else "inline"};" />'
            )
        
        last_pos = pos + len(full_match)
    
    # Add remaining text
    html_parts.append(text[last_pos:].replace('\n', '<br>'))
    
    # Wrap in minimal HTML
    html = ''.join(html_parts)
    
    # Gmail expects a specific structure
    full_html = f'''<div dir="ltr">{html}</div>'''
    
    return full_html


def copy_rich_html_to_clipboard(html: str, text: str) -> bool:
    """Copy HTML to clipboard in a way Gmail recognizes.
    
    This needs to put both HTML and plain text on the clipboard.
    """
    system = platform.system()
    
    if system == "Linux":
        try:
            # Create a script that copies both HTML and text
            script = f'''#!/bin/bash
echo -n '{text}' | xclip -selection clipboard -t text/plain
echo -n '{html}' | xclip -selection clipboard -t text/html
'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            subprocess.run(['chmod', '+x', script_path])
            result = subprocess.run([script_path], capture_output=True)
            subprocess.run(['rm', script_path])
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error: {e}")
            return False
            
    elif system == "Darwin":  # macOS
        try:
            # On macOS, we need to use osascript with HTML
            script = f'''
            set the clipboard to "{text}"
            do shell script "echo '{html}' | pbcopy"
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
            
    elif system == "Windows":
        try:
            # Windows requires special handling for HTML clipboard
            import win32clipboard
            
            # HTML clipboard format header
            html_header = """Version:0.9
StartHTML:00000097
EndHTML:{end_html:08d}
StartFragment:00000131
EndFragment:{end_fragment:08d}
<html>
<body>
<!--StartFragment-->{html}<!--EndFragment-->
</body>
</html>"""
            
            fragment = html
            full_html = html_header.format(
                html=fragment,
                end_fragment=len(html_header) - 76 + len(fragment),
                end_html=len(html_header) - 36 + len(fragment)
            )
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            
            # Set both text and HTML formats
            win32clipboard.SetClipboardText(text)
            win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat("HTML Format"), 
                                          full_html.encode('utf-8'))
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            return False
    
    return False