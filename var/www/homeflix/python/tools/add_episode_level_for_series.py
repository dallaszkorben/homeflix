#!/usr/bin/env python3

import os
import sys
import yaml
import argparse
from pathlib import Path

def process_card_file(file_path):
    """Process a single card.yaml file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Load YAML data
        data = yaml.safe_load(content)
        
        modified = False
        
        # Check if 'level' exists at top level
        if 'level' not in data:
            # Find position to insert 'level: episode' before 'sequence'
            lines = content.split('\n')
            new_lines = []
            
            for i, line in enumerate(lines):
                if line.strip().startswith('sequence:'):
                    new_lines.append('level: episode')
                    modified = True
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        # Check and modify title.showsequence
        if 'title' in data and isinstance(data['title'], dict) and 'showsequence' in data['title']:
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if 'showsequence:' in line and ':' in line:
                    # Keep the key but remove the value
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + 'showsequence:')
                    modified = True
                else:
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Modified: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_directory(directory):
    """Recursively process all card.yaml files in directory"""
    directory = Path(directory)
    modified_count = 0
    
    for card_file in directory.rglob('card.yaml'):
        if process_card_file(card_file):
            modified_count += 1
    
    return modified_count

def main():
    parser = argparse.ArgumentParser(description='Add episode level to series card.yaml files')
    parser.add_argument('directory', help='Directory to process recursively')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    print(f"Processing directory: {args.directory}")
    modified_count = process_directory(args.directory)
    print(f"Modified {modified_count} files")

if __name__ == '__main__':
    main()