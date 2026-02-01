#!/usr/bin/env python3
"""
ROSETTA Edge Case Test Runner
Tests translator against challenging markdown structures
"""

import sys
import subprocess
from pathlib import Path
from difflib import unified_diff


class TestRunner:
    """Run translation tests and check for issues"""
    
    def __init__(self, rosetta_script, test_file, target_lang='fr'):
        self.rosetta = Path(rosetta_script)
        self.test_file = Path(test_file)
        self.target_lang = target_lang
        self.issues = []
    
    def run_translation(self):
        """Run translator and capture output"""
        print(f"Testing: {self.test_file} -> {self.target_lang}")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.rosetta), self.target_lang, str(self.test_file), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.issues.append(f"Translation failed with exit code {result.returncode}")
                self.issues.append(f"Error: {result.stderr}")
                return None
            
            return result.stdout
        
        except subprocess.TimeoutExpired:
            self.issues.append("Translation timed out (>30 seconds)")
            return None
        
        except Exception as e:
            self.issues.append(f"Translation crashed: {e}")
            return None
    
    def check_structure(self, original, translated):
        """Check that structure is preserved"""
        print("\nStructure Checks:")
        print("-" * 60)
        
        import re
        
        # Count structural elements
        # For horizontal rules, count standalone ---, ***, or ___ lines
        def count_horizontal_rules(text):
            return len(re.findall(r'^(---+|\*\*\*+|___+)\s*$', text, re.MULTILINE))
        
        # For links, count actual markdown links [text](url), not just [ characters
        def count_links(text):
            return len(re.findall(r'\[[^\]]*\]\([^)]+\)', text))
        
        checks = [
            ("Code fences", lambda t: t.count("```")),
            ("Tables", lambda t: t.count("|")),
            ("Headers", lambda t: t.count("#")),
            ("Horizontal rules", count_horizontal_rules),
            ("Blockquotes", lambda t: t.count(">")),
            ("Links", count_links),
        ]
        
        for name, counter in checks:
            orig_count = counter(original)
            trans_count = counter(translated)
            
            status = "✓" if orig_count == trans_count else "✗"
            print(f"  {status} {name:20s}: {orig_count:3d} -> {trans_count:3d}")
            
            if orig_count != trans_count:
                self.issues.append(f"{name} count mismatch: {orig_count} != {trans_count}")
    
    def check_code_preservation(self, original, translated):
        """Check that code blocks are preserved exactly"""
        print("\nCode Preservation:")
        print("-" * 60)
        
        import re
        
        # Extract code blocks
        orig_blocks = re.findall(r'```[\s\S]*?```', original)
        trans_blocks = re.findall(r'```[\s\S]*?```', translated)
        
        print(f"  Code blocks found: {len(orig_blocks)} -> {len(trans_blocks)}")
        
        if len(orig_blocks) != len(trans_blocks):
            self.issues.append(f"Code block count mismatch: {len(orig_blocks)} != {len(trans_blocks)}")
            return
        
        mismatches = 0
        for i, (orig, trans) in enumerate(zip(orig_blocks, trans_blocks)):
            if orig != trans:
                mismatches += 1
                print(f"  ✗ Block {i+1} differs")
                if mismatches <= 3:  # Only show first 3
                    self.issues.append(f"Code block {i+1} modified:\n  Original: {orig[:50]}...\n  Translated: {trans[:50]}...")
        
        if mismatches == 0:
            print(f"  ✓ All {len(orig_blocks)} code blocks preserved")
        else:
            print(f"  ✗ {mismatches}/{len(orig_blocks)} code blocks differ")
    
    def check_inline_code(self, original, translated):
        """Check inline code preservation"""
        print("\nInline Code:")
        print("-" * 60)
        
        import re
        
        def extract_inline_code(text):
            """Extract inline code, excluding code fences and multiline content."""
            # First, remove code fences entirely to avoid matching their backticks
            text_no_fences = re.sub(r'```[\s\S]*?```', '', text)
            # Match single backtick pairs that don't contain newlines (true inline code)
            return re.findall(r'`[^`\n]+`', text_no_fences)
        
        orig_code = extract_inline_code(original)
        trans_code = extract_inline_code(translated)
        
        print(f"  Inline code: {len(orig_code)} -> {len(trans_code)}")
        
        # Sample check - first 10
        orig_sample = set(orig_code[:10])
        trans_sample = set(trans_code[:10])
        
        if orig_sample == trans_sample:
            print(f"  ✓ Sample inline code preserved")
        else:
            missing = orig_sample - trans_sample
            if missing:
                print(f"  ✗ Missing inline code: {missing}")
                self.issues.append(f"Inline code lost: {missing}")
    
    def check_math(self, original, translated):
        """Check math preservation"""
        print("\nMath Preservation:")
        print("-" * 60)
        
        import re
        
        # Extract inline math
        orig_inline = re.findall(r'\$[^$]+\$', original)
        trans_inline = re.findall(r'\$[^$]+\$', translated)
        
        print(f"  Inline math: {len(orig_inline)} -> {len(trans_inline)}")
        
        # Extract block math
        orig_block = re.findall(r'\$\$[\s\S]*?\$\$', original)
        trans_block = re.findall(r'\$\$[\s\S]*?\$\$', translated)
        
        print(f"  Block math: {len(orig_block)} -> {len(trans_block)}")
        
        # Check exact preservation
        if orig_inline == trans_inline and orig_block == trans_block:
            print(f"  ✓ All math preserved")
        else:
            print(f"  ✗ Math differs")
            self.issues.append("Math not preserved exactly")
    
    def check_tables(self, original, translated):
        """Check table structure"""
        print("\nTable Structure:")
        print("-" * 60)
        
        import re
        
        # Find table separators
        orig_seps = re.findall(r'\|[\s-]+\|', original)
        trans_seps = re.findall(r'\|[\s-]+\|', translated)
        
        print(f"  Table separators: {len(orig_seps)} -> {len(trans_seps)}")
        
        if len(orig_seps) == len(trans_seps):
            print(f"  ✓ Table count preserved")
        else:
            print(f"  ✗ Table count differs")
            self.issues.append(f"Table separator mismatch: {len(orig_seps)} != {len(trans_seps)}")
        
        # Check each separator has same column count
        for i, (orig, trans) in enumerate(zip(orig_seps, trans_seps)):
            orig_cols = orig.count('|') - 1
            trans_cols = trans.count('|') - 1
            if orig_cols != trans_cols:
                print(f"  ✗ Table {i+1}: {orig_cols} cols -> {trans_cols} cols")
                self.issues.append(f"Table {i+1} column mismatch")
    
    def run_all_checks(self):
        """Run all tests"""
        # Read original
        with open(self.test_file, 'r', encoding='utf-8') as f:
            original = f.read()
        
        # Run translation
        translated = self.run_translation()
        
        if translated is None:
            print("\n" + "=" * 60)
            print("TRANSLATION FAILED")
            self.print_issues()
            return False
        
        # Run checks
        self.check_structure(original, translated)
        self.check_code_preservation(original, translated)
        self.check_inline_code(original, translated)
        self.check_math(original, translated)
        self.check_tables(original, translated)
        
        # Summary
        print("\n" + "=" * 60)
        if self.issues:
            print(f"FAILED: {len(self.issues)} issues found")
            self.print_issues()
            return False
        else:
            print("PASSED: All checks passed ✓")
            return True
    
    def print_issues(self):
        """Print all issues found"""
        if not self.issues:
            return
        
        print("\nIssues:")
        for i, issue in enumerate(self.issues, 1):
            print(f"  {i}. {issue}")


def main():
    """Run edge case tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ROSETTA translator edge cases')
    parser.add_argument('--rosetta', default='tools/rosetta.py',
                       help='Path to rosetta.py')
    parser.add_argument('--test', default='tests/test_edge_cases.md',
                       help='Test file')
    parser.add_argument('--lang', default='fr',
                       help='Target language')
    
    args = parser.parse_args()
    
    runner = TestRunner(args.rosetta, args.test, args.lang)
    success = runner.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
