"""Tests for the CLI interface."""

import pytest
from click.testing import CliRunner
from mathrender.cli import main


class TestCLI:
    """Test the command-line interface."""
    
    def test_cli_help(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'LaTeX Email' in result.output
    
    def test_convert_help(self):
        """Test convert command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['convert', '--help'])
        assert result.exit_code == 0
        assert 'Convert LaTeX expressions' in result.output
    
    def test_convert_simple_text(self):
        """Test converting simple text without LaTeX."""
        runner = CliRunner()
        result = runner.invoke(main, ['convert', 'Simple text without math'])
        assert result.exit_code == 0
        # Should output base64 MIME
        assert len(result.output) > 0
    
    def test_convert_from_stdin(self):
        """Test converting from stdin."""
        runner = CliRunner()
        result = runner.invoke(main, ['convert'], input='Text from stdin')
        assert result.exit_code == 0
        assert len(result.output) > 0
    
    def test_convert_empty_input(self):
        """Test error on empty input."""
        runner = CliRunner()
        result = runner.invoke(main, ['convert'], input='')
        assert result.exit_code == 1
        assert 'No input provided' in result.output
    
    def test_convert_with_options(self):
        """Test convert with various options."""
        runner = CliRunner()
        result = runner.invoke(main, [
            'convert',
            'Test text',
            '--subject', 'My Subject',
            '--from', 'sender@test.com',
            '--to', 'recipient@test.com',
            '--dpi', '150'
        ])
        assert result.exit_code == 0
    
    def test_convert_raw_output(self):
        """Test raw MIME output."""
        runner = CliRunner()
        result = runner.invoke(main, ['convert', 'Test', '--raw'])
        assert result.exit_code == 0
        # Raw output should contain MIME headers
        assert 'Content-Type:' in result.output or 'MIME-Version:' in result.output
    
    def test_convert_to_file(self):
        """Test output to file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [
                'convert',
                'Test content',
                '--output', 'output.mime'
            ])
            assert result.exit_code == 0
            assert 'output.mime' in result.output
            
            # Check file was created
            import os
            assert os.path.exists('output.mime')
    
    def test_check_command(self):
        """Test dependency check command."""
        runner = CliRunner()
        result = runner.invoke(main, ['check'])
        # Don't check exit code as it depends on system deps
        assert 'LaTeX distribution' in result.output
        assert 'dvipng' in result.output
    
    def test_convert_with_latex_skip_if_no_deps(self):
        """Test LaTeX conversion (skip if dependencies missing)."""
        runner = CliRunner()
        result = runner.invoke(main, ['convert', 'Test $x^2$'])
        
        # If LaTeX deps are missing, might fail
        if result.exit_code != 0:
            assert ('LaTeX compilation failed' in result.output or 
                   'dvipng' in result.output)
        else:
            # Should have processed successfully
            assert len(result.output) > 0
    
    def test_clipboard_functionality(self):
        """Test clipboard copy functionality."""
        # Test the copy_to_clipboard function
        # This might fail on systems without clipboard support
        success = copy_to_clipboard("Test content")
        # Just verify it returns a boolean
        assert isinstance(success, bool)