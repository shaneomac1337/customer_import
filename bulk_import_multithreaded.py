import json
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import logging
from typing import List, Dict, Any
import queue

class BulkCustomerImporter:
    def __init__(self,
                 api_url: str,
                 auth_token: str,
                 gk_passport: str,
                 batch_size: int = 70,
                 max_workers: int = 5,
                 delay_between_requests: float = 1.0,
                 max_retries: int = 3,
                 progress_callback=None):
        
        self.api_url = api_url
        self.auth_token = auth_token
        self.gk_passport = gk_passport
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
        self.max_retries = max_retries
        self.progress_callback = progress_callback
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bulk_import.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self.total_batches = 0
        self.completed_batches = 0
        self.failed_batches = []
        self.lock = threading.Lock()
        
        # Rate limiting
        self.last_request_time = 0
        self.rate_limit_lock = threading.Lock()
    
    def load_customer_data(self, file_path: str) -> List[Dict[Any, Any]]:
        """Load customer data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('data', [])
        except Exception as e:
            self.logger.error(f"Error loading file {file_path}: {e}")
            return []
    
    def create_batches(self, customers: List[Dict[Any, Any]]) -> List[List[Dict[Any, Any]]]:
        """Split customers into batches of specified size"""
        batches = []
        for i in range(0, len(customers), self.batch_size):
            batch = customers[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def rate_limit(self):
        """Implement rate limiting between requests"""
        with self.rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.delay_between_requests:
                sleep_time = self.delay_between_requests - time_since_last
                time.sleep(sleep_time)
            self.last_request_time = time.time()
    
    def send_batch(self, batch: List[Dict[Any, Any]], batch_id: int) -> Dict[str, Any]:
        """Send a single batch to the API"""
        
        # Rate limiting
        self.rate_limit()
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'GK-Passport': self.gk_passport,
            'Content-Type': 'application/json'
        }
        
        payload = {'data': batch}
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Sending batch {batch_id} (attempt {attempt + 1}/{self.max_retries}) - {len(batch)} customers")
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60  # 60 second timeout
                )
                
                if response.status_code == 200:
                    with self.lock:
                        self.completed_batches += 1

                    # Parse response
                    response_data = {}
                    try:
                        if response.content:
                            response_data = response.json()
                    except json.JSONDecodeError:
                        response_data = {'raw_response': response.text}

                    self.logger.info(f"✅ Batch {batch_id} completed successfully - {self.completed_batches}/{self.total_batches}")

                    # Send progress update with API response details
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        self.progress_callback({
                            'type': 'batch_success',
                            'batch_id': batch_id,
                            'customers_count': len(batch),
                            'response_data': response_data,
                            'status_code': response.status_code,
                            'response_headers': dict(response.headers)
                        })

                    return {
                        'batch_id': batch_id,
                        'status': 'success',
                        'customers_count': len(batch),
                        'response': response_data,
                        'status_code': response.status_code,
                        'response_headers': dict(response.headers)
                    }
                else:
                    # Parse error response
                    error_data = {}
                    try:
                        if response.content:
                            error_data = response.json()
                    except json.JSONDecodeError:
                        error_data = {'raw_response': response.text}

                    self.logger.warning(f"⚠️ Batch {batch_id} failed with status {response.status_code}: {response.text}")

                    # Send progress update with API error details
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        self.progress_callback({
                            'type': 'batch_error',
                            'batch_id': batch_id,
                            'customers_count': len(batch),
                            'error_data': error_data,
                            'status_code': response.status_code,
                            'response_headers': dict(response.headers),
                            'attempt': attempt + 1,
                            'max_retries': self.max_retries
                        })

                    if attempt == self.max_retries - 1:  # Last attempt
                        with self.lock:
                            self.failed_batches.append({
                                'batch_id': batch_id,
                                'customers': batch,
                                'error': f"HTTP {response.status_code}: {response.text}",
                                'error_data': error_data,
                                'status_code': response.status_code
                            })
                        return {
                            'batch_id': batch_id,
                            'status': 'failed',
                            'error': f"HTTP {response.status_code}: {response.text}",
                            'error_data': error_data,
                            'status_code': response.status_code,
                            'response_headers': dict(response.headers)
                        }
                    else:
                        # Wait before retry
                        time.sleep(2 ** attempt)  # Exponential backoff
                        
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏰ Batch {batch_id} timed out (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    with self.lock:
                        self.failed_batches.append({
                            'batch_id': batch_id,
                            'customers': batch,
                            'error': 'Request timeout'
                        })
                    return {
                        'batch_id': batch_id,
                        'status': 'failed',
                        'error': 'Request timeout'
                    }
                else:
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                self.logger.error(f"❌ Batch {batch_id} error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    with self.lock:
                        self.failed_batches.append({
                            'batch_id': batch_id,
                            'customers': batch,
                            'error': str(e)
                        })
                    return {
                        'batch_id': batch_id,
                        'status': 'failed',
                        'error': str(e)
                    }
                else:
                    time.sleep(2 ** attempt)
    
    def import_customers(self, file_paths: List[str]) -> Dict[str, Any]:
        """Import customers from multiple files using multithreading"""
        
        start_time = datetime.now()
        self.logger.info(f"🚀 Starting bulk import from {len(file_paths)} files")
        
        # Load all customer data
        all_customers = []
        for file_path in file_paths:
            customers = self.load_customer_data(file_path)
            all_customers.extend(customers)
            self.logger.info(f"Loaded {len(customers)} customers from {file_path}")
        
        if not all_customers:
            self.logger.error("No customer data loaded!")
            return {'status': 'error', 'message': 'No customer data loaded'}
        
        # Create batches
        batches = self.create_batches(all_customers)
        self.total_batches = len(batches)
        
        self.logger.info(f"📦 Created {self.total_batches} batches of {self.batch_size} customers each")
        self.logger.info(f"🔧 Using {self.max_workers} worker threads")
        
        # Process batches with thread pool
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(self.send_batch, batch, i): i 
                for i, batch in enumerate(batches, 1)
            }
            
            # Process completed batches
            for future in as_completed(future_to_batch):
                batch_id = future_to_batch[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ Batch {batch_id} failed with exception: {e}")
                    results.append({
                        'batch_id': batch_id,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        # Calculate final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        successful_batches = len([r for r in results if r.get('status') == 'success'])
        failed_batches = len([r for r in results if r.get('status') == 'failed'])
        
        total_customers = len(all_customers)
        successful_customers = successful_batches * self.batch_size
        
        summary = {
            'status': 'completed',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'total_customers': total_customers,
            'total_batches': self.total_batches,
            'successful_batches': successful_batches,
            'failed_batches': failed_batches,
            'successful_customers': successful_customers,
            'failed_customers': failed_batches * self.batch_size,
            'success_rate': f"{(successful_batches/self.total_batches)*100:.1f}%"
        }
        
        self.logger.info("📊 IMPORT SUMMARY:")
        self.logger.info(f"   Total customers: {total_customers}")
        self.logger.info(f"   Successful: {successful_customers}")
        self.logger.info(f"   Failed: {failed_batches * self.batch_size}")
        self.logger.info(f"   Success rate: {summary['success_rate']}")
        self.logger.info(f"   Duration: {duration}")
        
        # Save failed batches for retry
        if self.failed_batches:
            self.save_failed_batches()
        
        return summary
    
    def save_failed_batches(self):
        """Save failed batches to a file for retry"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_file = f"failed_batches_{timestamp}.json"
        
        failed_data = {
            'timestamp': timestamp,
            'failed_batches': self.failed_batches
        }
        
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Saved {len(self.failed_batches)} failed batches to {failed_file}")

# Example usage function
def main():
    # Configuration
    API_URL = "https://prod.cse.cloud4retail.co/customer-profile-service/tenants/001/services/rest/customers-import/v1/customers"
    AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im9hdXRoMi5rZXkuMSJ9..."  # Your full token
    GK_PASSPORT = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg=="
    
    # Initialize importer
    importer = BulkCustomerImporter(
        api_url=API_URL,
        auth_token=AUTH_TOKEN,
        gk_passport=GK_PASSPORT,
        batch_size=70,          # Sweet spot batch size
        max_workers=3,          # Start conservative with 3 threads
        delay_between_requests=0.5,  # 500ms between requests
        max_retries=3
    )
    
    # Files to import
    files_to_import = [
        "customers_70_random.json",
        # Add more files as needed
        # "customers_70_random_batch2.json",
        # "customers_70_random_batch3.json",
    ]
    
    # Run the import
    result = importer.import_customers(files_to_import)
    
    print("\n" + "="*50)
    print("BULK IMPORT COMPLETED")
    print("="*50)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()