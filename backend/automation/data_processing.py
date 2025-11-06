"""
Data processing utilities for file conversion and management.
Handles Excel to JSON conversion, file organization, and data extraction.
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
import pandas as pd


def sanitize_filename(name: str, max_len: int = 180) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid = '<>:"/\\|?*'
    cleaned = name.translate(str.maketrans({ch: "_" for ch in invalid}))
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.strip(" .")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" ._")
    return cleaned


def unique_path(base: Path) -> Path:
    """Generate unique file path if file already exists."""
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    i = 1
    while True:
        candidate = base.with_name(f"{stem} ({i}){suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def convert_excel_to_json(excel_path: Path, downloads_folder: Path) -> Path:
    """
    Convert Excel file (including HTML format) to JSON format.
    
    Args:
        excel_path: Path to Excel file to convert
        downloads_folder: Target folder for JSON output
        
    Returns:
        Path to created JSON file
    """
    try:
        print(f"Converting Excel file: {excel_path}")
        
        # Check if file is HTML format (common with web exports)
        with open(excel_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        
        df = None
        
        if first_line.startswith('<!DOCTYPE') or first_line.startswith('<html'):
            print("File appears to be HTML format, trying to parse as HTML table...")
            df = _parse_html_table(excel_path)
        else:
            print("File appears to be binary Excel, trying Excel engines...")
            df = _parse_excel_file(excel_path)
        
        if df is None:
            raise Exception("Could not read Excel file with any available engine")
        
        print(f"Excel file contains {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        
        # Create JSON path in downloads folder
        json_filename = excel_path.stem + '.json'
        json_path = downloads_folder / json_filename
        
        # Convert DataFrame to JSON
        json_data = df.to_json(orient='records', indent=2, date_format='iso', force_ascii=False)
        
        # Write JSON to downloads folder
        with open(json_path, 'w', encoding='utf-8') as f:
            data = json.loads(json_data)
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted {excel_path.name} to {json_path}")
        
        # Show sample of data
        if data:
            print(f"Sample data (first 3 rows):")
            for i, record in enumerate(data[:3]):
                print(f"Row {i+1}: {record}")
        
        return json_path
        
    except Exception as e:
        print(f"Error converting Excel to JSON: {e}")
        # Copy original Excel file to downloads folder as fallback
        try:
            excel_copy_path = downloads_folder / excel_path.name
            excel_path.rename(excel_copy_path)
            print(f"Excel file moved to: {excel_copy_path}")
            return excel_copy_path
        except Exception as copy_error:
            print(f"Error copying Excel file: {copy_error}")
            return excel_path


def _parse_html_table(excel_path: Path) -> pd.DataFrame:
    """Parse HTML table from Excel export file."""
    try:
        # Method 1: Try pandas read_html first
        try:
            print("Trying pandas read_html...")
            tables = pd.read_html(excel_path)
            if tables:
                df = tables[0]
                print(f"Successfully read HTML table with pandas, {len(df)} rows")
                return df
        except Exception as e1:
            print(f"Pandas read_html failed: {e1}")
        
        # Method 2: Manual regex table extraction
        try:
            print("Trying manual regex table extraction...")
            
            with open(excel_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Find table content between <table> tags
            table_pattern = r'<table[^>]*>(.*?)</table>'
            table_matches = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if table_matches:
                print(f"Found {len(table_matches)} table(s) with regex")
                
                # Extract rows from first table
                table_html = table_matches[0]
                row_pattern = r'<tr[^>]*>(.*?)</tr>'
                row_matches = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)
                
                if row_matches:
                    rows = []
                    for row_html in row_matches:
                        cell_pattern = r'<t[hd][^>]*>(.*?)</t[hd]>'
                        cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
                        
                        # Clean up cell text
                        clean_cells = []
                        for cell in cells:
                            clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                            clean_cells.append(clean_text)
                        
                        if clean_cells:
                            rows.append(clean_cells)
                    
                    if rows:
                        headers = rows[0] if rows else None
                        data_rows = rows[1:] if len(rows) > 1 else rows
                        
                        df = pd.DataFrame(data_rows, columns=headers)
                        print(f"Successfully extracted HTML table with regex, {len(df)} rows, {len(df.columns)} columns")
                        return df
                    else:
                        print("No data extracted with regex")
                else:
                    print("No table rows found with regex")
            else:
                print("No tables found with regex")
                
        except Exception as e2:
            print(f"Manual regex extraction failed: {e2}")
            
    except Exception as e:
        print(f"HTML parsing failed: {e}")
    
    return None


def _parse_excel_file(excel_path: Path) -> pd.DataFrame:
    """Parse binary Excel file using various engines."""
    engines_to_try = ['openpyxl', 'xlrd', None]  # None lets pandas auto-detect
    
    for engine in engines_to_try:
        try:
            print(f"Trying to read Excel with engine: {engine}")
            if engine:
                df = pd.read_excel(excel_path, engine=engine)
            else:
                df = pd.read_excel(excel_path)
            print(f"Successfully read Excel file with engine: {engine}")
            return df
        except Exception as e:
            print(f"Engine {engine} failed: {e}")
            continue
    
    return None


def manage_output_folders():
    """Manage downloads and historic outputs folders."""
    downloads_folder = Path.cwd() / "downloads"
    historic_folder = Path.cwd() / "historic_outputs"
    
    downloads_folder.mkdir(exist_ok=True)
    historic_folder.mkdir(exist_ok=True)
    
    # Move existing files from downloads to historic_outputs
    if downloads_folder.exists():
        existing_files = list(downloads_folder.glob("*"))
        if existing_files:
            print(f"Moving {len(existing_files)} existing files to historic_outputs...")
            
            # Create timestamped subfolder in historic_outputs
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            historic_session_folder = historic_folder / f"session_{timestamp}"
            historic_session_folder.mkdir(exist_ok=True)
            
            moved_count = 0
            for file_path in existing_files:
                if file_path.is_file():
                    try:
                        new_path = historic_session_folder / file_path.name
                        file_path.rename(new_path)
                        moved_count += 1
                    except Exception as e:
                        print(f"Could not move {file_path.name}: {e}")
            
            if moved_count > 0:
                print(f"✅ Moved {moved_count} files to: {historic_session_folder}")
    
    return downloads_folder, historic_folder


def get_clients_from_json_file(json_file_path: Path):
    """Extract unique clients from a specific JSON file."""
    clients = []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📋 Processing JSON file: {json_file_path.name}")
        print(f"Total records in JSON: {len(data)}")
        
        for i, record in enumerate(data):
            # Handle None values properly - get the value and only strip if not None
            first_name = record.get('FirstName', '') or ''
            last_name = record.get('LastName', '') or ''
            first_name = first_name.strip() if first_name else ''
            last_name = last_name.strip() if last_name else ''
            
            # Clean up last names - remove common suffixes like "ECM" if they appear
            cleaned_last_name = last_name
            if last_name.endswith(' ECM'):
                cleaned_last_name = last_name.replace(' ECM', '').strip()
                print(f"   Cleaned LastName: '{last_name}' → '{cleaned_last_name}'")
            
            # Skip empty names or placeholders
            if (first_name and cleaned_last_name and 
                first_name not in ['&nbsp;', ''] and 
                cleaned_last_name not in ['&nbsp;', '']):
                
                client_info = {
                    'first_name': first_name,
                    'last_name': cleaned_last_name,
                    'original_last_name': last_name,
                    'full_name': f"{cleaned_last_name}, {first_name}",
                    'record_index': i
                }
                
                # Check if this client is already in our list
                if not any(c['full_name'] == client_info['full_name'] for c in clients):
                    clients.append(client_info)
                    if len(clients) <= 5:  # Show first 5 for debugging
                        print(f"   Added client #{len(clients)}: {client_info['full_name']}")
                    
    except Exception as e:
        print(f"Error reading {json_file_path}: {e}")
        import traceback
        traceback.print_exc()
    
    result = sorted(clients, key=lambda x: x['full_name'])
    print(f"✅ Found {len(result)} unique clients to process")
    
    return result


def get_available_clients():
    """Get list of clients from JSON files in downloads folder."""
    downloads_folder = Path.cwd() / "downloads"
    clients = []
    
    if downloads_folder.exists():
        json_files = list(downloads_folder.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for record in data:
                    # Handle None values properly
                    first_name = record.get('FirstName', '') or ''
                    last_name = record.get('LastName', '') or ''
                    first_name = first_name.strip() if first_name else ''
                    last_name = last_name.strip() if last_name else ''
                    
                    # Skip empty names or placeholders
                    if (first_name and last_name and 
                        first_name not in ['&nbsp;', ''] and 
                        last_name not in ['&nbsp;', '']):
                        
                        # Use original last name for display (no cleaning for manual search)
                        client_name = f"{last_name}, {first_name}"
                        if client_name not in clients:
                            clients.append(client_name)
                            
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
                continue
    
    return sorted(clients)


def get_original_name_for_search(display_name):
    """Get the original last name for search purposes from a display name."""
    if ", " not in display_name:
        return None, None
        
    last_name, first_name = display_name.split(", ", 1)
    
    # For manual search, the display_name already contains the original name
    return last_name, first_name


def update_json_with_personal_data(json_file_path: Path, client_name: str, extracted_data: dict) -> bool:
    """
    Update the JSON file with extracted personal data for a specific client.
    
    Args:
        json_file_path: Path to the JSON file
        client_name: Client name in format "LastName, FirstName"
        extracted_data: Dictionary containing extracted personal data
    
    Returns:
        True if update was successful, False otherwise
    """
    try:
        # Parse client name
        if ", " not in client_name:
            print(f"❌ Invalid client name format: {client_name}")
            return False
        
        # Split the cleaned display name
        display_last, display_first = client_name.split(", ", 1)
        
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Track if any records were updated
        updated_count = 0
        
        # Update matching records
        for record in data:
            # Handle None values properly
            record_first = record.get('FirstName', '') or ''
            record_last = record.get('LastName', '') or ''
            record_first = record_first.strip() if record_first else ''
            record_last = record_last.strip() if record_last else ''
            
            # Skip records with empty names
            if not record_first or not record_last:
                continue
            
            # Clean the record's last name for comparison (remove ECM suffix)
            cleaned_record_last = record_last.replace(' ECM', '').strip() if record_last.endswith(' ECM') else record_last
            
            # Check if this record matches the client
            if (record_first.lower() == display_first.lower() and 
                cleaned_record_last.lower() == display_last.lower()):
                
                # Add extracted personal data to the record
                record['personal_data'] = {
                    'phone_1': extracted_data.get('phone_1', ''),
                    'phone_2': extracted_data.get('phone_2', ''),
                    'service_start': extracted_data.get('service_start', ''),
                    'service_end': extracted_data.get('service_end', ''),
                    'inquiry_date': extracted_data.get('inquiry_date', ''),
                    'assessment': extracted_data.get('assessment', ''),
                    'case_manager': extracted_data.get('case_manager', ''),
                    'med_record': extracted_data.get('med_record', ''),
                    'referral_number': extracted_data.get('referral_number', ''),
                    'address_1': extracted_data.get('address_1', ''),
                    'address_2': extracted_data.get('address_2', ''),
                    'city': extracted_data.get('city', ''),
                    'state': extracted_data.get('state', ''),
                    'zip': extracted_data.get('zip', ''),
                    'county': extracted_data.get('county', '')
                }
                
                updated_count += 1
        
        if updated_count > 0:
            # Write the updated data back to the file
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated {updated_count} record(s) in JSON for {client_name}")
            return True
        else:
            print(f"⚠️ No matching records found in JSON for {client_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating JSON file: {e}")
        import traceback
        traceback.print_exc()
        return False
