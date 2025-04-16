import pandas as pd
import requests
import os
from urllib.parse import urlparse
import time
import random

# Set pandas to display full URLs
pd.set_option('display.max_colwidth', None)
# Settings Paths
BASE_PATH = os.path.join(os.getcwd(), "data")
excel_file = BASE_PATH + "\\generales-banco.xlsx"
output_dir = BASE_PATH + "\\FILES"
url_column = "Sitio-Web"

def download_file(url, download_path, max_retries=3):
    """
    Download a file from a URL to the specified path with retry logic
    
    Args:
        url (str): The URL of the file to download
        download_path (str): The path where the file will be saved
        max_retries (int): Maximum number of retry attempts
    
    Returns:
        bool: True if download was successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Send a GET request to the URL with increased timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # Increase timeout to 60 seconds to handle slower connections
            response = requests.get(url, stream=True, timeout=60, headers=headers)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(download_path), exist_ok=True)
                
                # Write the content to a file
                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"Successfully downloaded: {url} to {download_path}")
                return True
            else:
                print(f"Failed to download {url}. Status code: {response.status_code}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    return False
        
        except requests.exceptions.Timeout:
            print(f"Timeout error downloading {url}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Max retries reached. Could not download {url} due to timeout")
                return False
        
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                return False

def get_filename_from_url(url, index):
    """
    Extract a filename from a URL, with fallback to index-based naming
    
    Args:
        url (str): The URL to extract the filename from
        index (int): Index to use if filename can't be determined
    
    Returns:
        str: The filename extracted from the URL
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Get the filename from the path
    filename = os.path.basename(path)
    
    # If no filename was found or it's empty, create a default one
    if not filename or filename == '/' or filename == '':
        # Use domain name + index for better identification
        domain = parsed_url.netloc.replace('www.', '')
        domain = ''.join(c if c.isalnum() else '_' for c in domain)
        filename = f"{domain}_{index}.html"
    
    # Replace invalid characters in the filename
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length to avoid path too long errors
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext if ext else name[:100]
        
    return filename

def main():
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Try to read the Excel file
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Check if the specified column exists
        if url_column not in df.columns:
            print(f"Column '{url_column}' not found in the Excel file.")
            print(f"Available columns: {', '.join(df.columns)}")
            return
        
        # Get all Bank Name and URLs from the column Nombre-Banco and Sitio-Web
        banks = df["Nombre-Banco"].dropna().tolist()
        urls = df[url_column].dropna().tolist()
        
        
        print(f"Found {len(urls)} URLs in column '{url_column}'")
        
        # Create a log file
        log_file = os.path.join(output_dir, "download_log.txt")
        
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write(f"Download log for {excel_file}, column {url_column}\n")
            log.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Download each URL
            for i, url in enumerate(urls):
                if not isinstance(url, str):
                    log.write(f"Skipping non-string URL at index {i}\n")
                    continue
                
                # Clean up the URL
                url = url.strip()
                if not url:
                    log.write(f"Skipping empty URL at index {i}\n")
                    continue
                
                # Add http:// prefix if missing
                if not url.startswith('http'):
                    url = 'http://' + url
                
                # Get filename from URL
                filename = get_filename_from_url(url, i)
                
                
                # For PDFs, make sure the extension is .pdf
                if '.pdf' in url.lower() and not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
                
                
                # Create download path (all files in same directory)
                #full_filename = clean_text(df["Nombre-Banco"]) + "_"+ filename
                #print(full_filename)
                download_path = os.path.join(output_dir,  filename)
                
                # Download the file
                print(f"({i+1}/{len(urls)}) Downloading: {url}")
                log.write(f"({i+1}/{len(urls)}) URL: {url}\n")
                
                success = download_file(url, download_path)
                log.write(f"    Result: {'Success' if success else 'Failed'}\n")
                log.write(f"    Path: {download_path}\n\n")
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(random.uniform(1.0, 3.0))
            
            log.write(f"\nDownload process completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write(f"Files saved to: {os.path.abspath(output_dir)}\n")
        
        print(f"\nAll downloads completed. Files saved to: {os.path.abspath(output_dir)}")
        print(f"Log file created at: {os.path.abspath(log_file)}")
    
    except FileNotFoundError:
        print(f"Excel file '{excel_file}' not found. Please make sure the file exists in the current directory.")
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")

if __name__ == "__main__":
    main()