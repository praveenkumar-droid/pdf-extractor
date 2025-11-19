"""
Example: Using the API with Python requests
"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))
    print()


def test_single_file_upload():
    """Test single file extraction"""
    print("Testing single file upload...")
    
    # Replace with your actual PDF path
    pdf_path = "input/sample.pdf"
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('sample.pdf', f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/extract", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Success!")
        print(f"  Characters: {result['statistics']['characters']}")
        print(f"  Lines: {result['statistics']['lines']}")
        print(f"  Preview: {result['text'][:200]}...")
    else:
        print(f"✗ Failed: {response.text}")
    print()


def test_batch_upload():
    """Test batch file extraction"""
    print("Testing batch upload...")
    
    # Replace with your actual PDF paths
    pdf_files = ["input/doc1.pdf", "input/doc2.pdf"]
    
    files = []
    for pdf_path in pdf_files:
        with open(pdf_path, 'rb') as f:
            files.append(('files', (pdf_path, f.read(), 'application/pdf')))
    
    response = requests.post(f"{BASE_URL}/extract/batch", files=files)
    
    if response.status_code == 200:
        result = response.json()
        job_id = result['job_id']
        print(f"✓ Batch job started: {job_id}")
        
        # Check status
        import time
        time.sleep(2)
        
        status_response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        print(f"  Status: {status_response.json()}")
    else:
        print(f"✗ Failed: {response.text}")
    print()


def test_folder_processing():
    """Test folder processing"""
    print("Testing folder processing...")
    
    response = requests.post(f"{BASE_URL}/extract/folder")
    
    if response.status_code == 200:
        result = response.json()
        job_id = result['job_id']
        print(f"✓ Folder processing started: {job_id}")
        print(f"  Check status at: {BASE_URL}/jobs/{job_id}")
    else:
        print(f"✗ Failed: {response.text}")
    print()


def test_list_files():
    """Test listing extracted files"""
    print("Testing file listing...")
    
    response = requests.get(f"{BASE_URL}/files/list")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Found {result['total']} files")
        for file in result['files'][:5]:  # Show first 5
            print(f"  - {file['filename']} ({file['size']} bytes)")
    else:
        print(f"✗ Failed: {response.text}")
    print()


def test_stats():
    """Test system statistics"""
    print("Testing system statistics...")
    
    response = requests.get(f"{BASE_URL}/stats")
    
    if response.status_code == 200:
        result = response.json()
        print("✓ System Statistics:")
        print(f"  Input PDFs: {result['input_pdfs']}")
        print(f"  Output Texts: {result['output_texts']}")
        print(f"  Active Jobs: {result['active_jobs']}")
    else:
        print(f"✗ Failed: {response.text}")
    print()


if __name__ == "__main__":
    print("="*60)
    print("PDF Extractor API - Test Client")
    print("="*60)
    print()
    
    # Run tests
    test_health()
    
    # Uncomment to test other endpoints
    # test_single_file_upload()
    # test_batch_upload()
    # test_folder_processing()
    # test_list_files()
    # test_stats()
    
    print("="*60)
    print("Tests completed!")
    print("="*60)
