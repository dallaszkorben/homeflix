#!/usr/bin/env python3
"""
HomeFlix Media Level Assignment Tool

This script automatically assigns appropriate 'level' attributes to media cards
in a HomeFlix media library based on their hierarchical position. It processes
card.yaml files recursively and adds level metadata to enable proper media
organization and playback behavior.

The tool follows HomeFlix's hierarchical structure:
- series/season → episode (for TV shows)
- band/lp → record (for music albums)

Only processes cards that don't already have a level attribute.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path

def get_card_level(card_path):
    """
    Extract the 'level' attribute from a card.yaml file.
    
    Args:
        card_path (Path): Path to the card.yaml file
        
    Returns:
        str or None: The level value if found, None otherwise
    """
    try:
        with open(card_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('level')
    except:
        return None

def process_card_file(file_path, parent_level):
    """
    Process a single card.yaml file by adding appropriate level attribute.
    
    Adds 'level: episode' for series/season parents or 'level: record' for
    band/lp parents. Also clears any existing showsequence values while
    preserving the key.
    
    Args:
        file_path (Path): Path to the card.yaml file to process
        parent_level (str): The level attribute of the parent directory
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = yaml.safe_load(content)
        
        # Only modify cards without existing level attribute and valid parent
        if 'level' not in data and parent_level in ['series', 'season', 'band', 'lp']:
            modified = False
            
            # Determine appropriate level based on parent hierarchy
            if parent_level in ['series', 'season']:
                level_to_add = 'episode'  # TV show episodes
            else:  # band or lp
                level_to_add = 'record'   # Music tracks
            
            # Insert level attribute before sequence attribute
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if line.strip().startswith('sequence:'):
                    new_lines.append(f'level: {level_to_add}')
                    modified = True
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
            
            # Clear showsequence values while keeping the key
            if 'title' in data and isinstance(data['title'], dict) and 'showsequence' in data['title']:
                lines = content.split('\n')
                new_lines = []
                
                for line in lines:
                    if 'showsequence:' in line and ':' in line:
                        # Preserve indentation but remove value
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + 'showsequence:')
                        modified = True
                    else:
                        new_lines.append(line)
                
                content = '\n'.join(new_lines)
            
            # Write changes back to file
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Modified: {file_path} (added level: {level_to_add})")
                return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_directory(directory, parent_level=None):
    """
    Recursively process directories and their card.yaml files.
    
    Traverses the directory tree, reading each directory's card.yaml to
    determine its level, then processes child directories accordingly.
    Only recurses into directories with container levels (series, season, band, lp).
    
    Args:
        directory (Path): Directory to process
        parent_level (str, optional): Level of the parent directory
        
    Returns:
        int: Number of files modified
    """
    directory = Path(directory)
    modified_count = 0
    
    # Read current directory's card.yaml to determine its level
    card_file = directory / 'card.yaml'
    current_level = None
    
    if card_file.exists():
        current_level = get_card_level(card_file)
        
        # Process this card if it has no level but parent is a container type
        if current_level is None and parent_level in ['series', 'season', 'band', 'lp']:
            if process_card_file(card_file, parent_level):
                modified_count += 1
    
    # Determine what level to pass to child directories
    # Use current directory's level if it exists, otherwise inherit from parent
    level_for_children = current_level if current_level is not None else parent_level
    
    # Recurse into subdirectories if current level allows it or we're at root
    if level_for_children in ['series', 'season', 'band', 'lp'] or parent_level is None:
        for subdir in directory.iterdir():
            if subdir.is_dir():
                modified_count += process_directory(subdir, level_for_children)
    
    return modified_count

def main():
    """
    Main entry point for the HomeFlix Media Level Assignment Tool.
    
    Parses command line arguments, validates input, and initiates the
    recursive directory processing.
    """
    parser = argparse.ArgumentParser(
        description='HomeFlix Media Level Assignment Tool - Automatically assign level attributes to media cards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
DESCRIPTION:
  This tool processes HomeFlix media libraries to automatically assign appropriate
  'level' attributes to media cards based on their hierarchical position. This
  enables proper media organization and playback behavior in the HomeFlix interface.

  The tool follows HomeFlix's content hierarchy:
  • TV Shows: series → season → episode (gets 'level: episode')
  • Music: band → lp → record (gets 'level: record')

  Only processes cards that don't already have a level attribute, ensuring
  existing configurations are preserved.

HOW IT WORKS:
  1. Starts from the specified root directory
  2. Reads each directory's card.yaml to determine its level
  3. Recursively processes subdirectories if parent is a container type
  4. Adds appropriate level attribute to media cards without existing levels
  5. Clears showsequence values while preserving the key structure

EXAMPLES:
  %(prog)s --path /media/music
  %(prog)s --path /media/tv-shows
  %(prog)s --path .

DIRECTORY STRUCTURE EXAMPLE:
  ./Music/
  ├── Beatles/                    (level: band)
  │   ├── Abbey Road/             (level: lp)
  │   │   ├── 01 - Come Together/ (no level → gets 'level: record')
  │   │   └── 02 - Something/     (no level → gets 'level: record')
  │   └── White Album/            (level: lp)
  └── Pink Floyd/                 (level: band)
        '''
    )
    
    parser.add_argument('--path', required=True, 
                       help='Root directory path to process recursively (required)')
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.path:
        parser.print_help()
        sys.exit(1)
    
    # Validate directory exists
    if not os.path.exists(args.path):
        print(f"Error: Directory '{args.path}' does not exist")
        sys.exit(1)
    
    # Start processing
    print(f"Processing directory: {args.path}")
    modified_count = process_directory(args.path, None)  # Start with no parent level
    print(f"Modified {modified_count} files")

if __name__ == '__main__':
    main()