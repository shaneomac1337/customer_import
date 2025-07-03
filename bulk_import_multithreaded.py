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
from auth_manager import AuthenticationManager

class BulkCustomerImporter:
    def __init__(self,
                 api_url: str,
                 auth_token: str = None,
                 gk_passport: str = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg==",
                 batch_size: int = 70,
                 max_workers: int = 5,
                 delay_between_requests: float = 1.0,
                 max_retries: int = 3,
                 progress_callback=None,
                 # New authentication parameters
                 username: str = "coop_sweden",
                 password: str = "coopsverige123",
                 use_auto_auth: bool = False,
                 # Failed customers tracking
                 failed_customers_file: str = "failed_customers.json"):

        self.api_url = api_url
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
        self.max_retries = max_retries
        self.progress_callback = progress_callback

        # Create failed_customers directory if it doesn't exist
        failed_customers_dir = "failed_customers"
        os.makedirs(failed_customers_dir, exist_ok=True)

        # Set failed customers file path in the dedicated folder
        if not os.path.dirname(failed_customers_file):
            # If no directory specified, put it in failed_customers folder
            self.failed_customers_file = os.path.join(failed_customers_dir, failed_customers_file)
        else:
            # If directory already specified, use as-is
            self.failed_customers_file = failed_customers_file

        # Failed customers tracking
        self.failed_customers = []
        self.failed_customers_lock = threading.Lock()

        # Authentication setup
        if use_auto_auth:
            # Use automatic authentication manager
            self.auth_manager = AuthenticationManager(
                username=username,
                password=password,
                gk_passport=gk_passport
            )
            self.auth_token = None  # Will be managed automatically
            self.gk_passport = gk_passport
        else:
            # Use manual token (legacy mode)
            self.auth_manager = None
            self.auth_token = auth_token
            self.gk_passport = gk_passport
        
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

    def test_authentication(self) -> Dict[str, Any]:
        """Test authentication (works with both manual and automatic modes)"""
        try:
            if self.auth_manager:
                # Test automatic authentication
                return self.auth_manager.test_authentication()
            else:
                # Test manual token
                headers = {
                    'Authorization': f'Bearer {self.auth_token}',
                    'GK-Passport': self.gk_passport,
                    'Content-Type': 'application/json'
                }

                # Simple test - just check if headers are valid format
                if not self.auth_token:
                    return {
                        'success': False,
                        'error': 'No auth token provided',
                        'message': 'Manual authentication failed'
                    }

                return {
                    'success': True,
                    'token_preview': f"{self.auth_token[:20]}..." if self.auth_token else None,
                    'message': 'Manual authentication configured'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Authentication test failed'
            }

    def get_auth_info(self) -> Dict[str, Any]:
        """Get information about current authentication setup"""
        if self.auth_manager:
            info = self.auth_manager.get_token_info()
            info['mode'] = 'automatic'
            return info
        else:
            return {
                'mode': 'manual',
                'has_token': bool(self.auth_token),
                'token_preview': f"{self.auth_token[:20]}..." if self.auth_token else None
            }
    
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

    def _parse_api_response_for_failures(self, response_data, batch_customers):
        """Parse API response to extract failed customers"""
        failed_customers = []

        try:
            if isinstance(response_data, str):
                response_json = json.loads(response_data)
            else:
                response_json = response_data

            # Look for customer results in the response - check both 'data' and 'customers' arrays
            customer_results = []
            if 'data' in response_json:
                customer_results = response_json['data']
            elif 'customers' in response_json:
                customer_results = response_json['customers']

            for customer_result in customer_results:
                if customer_result.get('result') == 'FAILED':
                    # Find the original customer data
                    customer_id = customer_result.get('customerId')
                    username = customer_result.get('username')

                    # Try to match with original batch data
                    original_customer = None
                    for customer in batch_customers:
                        if (customer.get('personalNumber') in username if username else False) or \
                           (customer.get('customerCards', [{}])[0].get('cardNumber') == customer_id):
                            original_customer = customer
                            break

                    failed_customer = {
                        'customerId': customer_id,
                        'username': username,
                        'result': customer_result.get('result'),
                        'error': customer_result.get('error', 'Unknown error'),
                        'timestamp': datetime.now().isoformat(),
                        'originalData': original_customer
                    }
                    failed_customers.append(failed_customer)

            # Also check for any other failure indicators in the response
            if 'errors' in response_json:
                for error in response_json['errors']:
                    failed_customer = {
                        'customerId': error.get('customerId', 'Unknown'),
                        'username': error.get('username', 'Unknown'),
                        'result': 'FAILED',
                        'error': error.get('message', str(error)),
                        'timestamp': datetime.now().isoformat(),
                        'originalData': None
                    }
                    failed_customers.append(failed_customer)

        except Exception as e:
            logging.error(f"Error parsing API response for failures: {e}")

        return failed_customers

    def _save_failed_customers(self, failed_customers):
        """Save failed customers to file"""
        if not failed_customers:
            return

        with self.failed_customers_lock:
            self.failed_customers.extend(failed_customers)

            # Save to file
            try:
                with open(self.failed_customers_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_customers, f, indent=2, ensure_ascii=False)
                logging.info(f"Saved {len(failed_customers)} failed customers to {self.failed_customers_file}")
            except Exception as e:
                logging.error(f"Error saving failed customers to file: {e}")

    def get_failed_customers_summary(self):
        """Get summary of failed customers"""
        with self.failed_customers_lock:
            total_failed = len(self.failed_customers)
            if total_failed == 0:
                return {
                    'total_failed': 0,
                    'failed_customers_file': self.failed_customers_file,
                    'summary': 'No failed customers'
                }

            # Group by error type
            error_types = {}
            for customer in self.failed_customers:
                error = customer.get('error', 'Unknown error')
                if error not in error_types:
                    error_types[error] = 0
                error_types[error] += 1

            return {
                'total_failed': total_failed,
                'failed_customers_file': self.failed_customers_file,
                'error_types': error_types,
                'recent_failures': self.failed_customers[-5:] if total_failed > 0 else []
            }
    
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

        # Get authentication headers (with automatic refresh if needed)
        if self.auth_manager:
            try:
                headers = self.auth_manager.get_auth_headers()
            except Exception as e:
                self.logger.error(f"❌ Authentication failed for batch {batch_id}: {e}")
                return {
                    'batch_id': batch_id,
                    'status': 'failed',
                    'error': f'Authentication failed: {e}'
                }
        else:
            # Legacy manual token mode
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
                    json=payload
                    # No timeout - let API handle its own timeout logic
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

                    # Check for failed customers within successful response
                    failed_customers = self._parse_api_response_for_failures(response_data, batch)
                    if failed_customers:
                        self._save_failed_customers(failed_customers)
                        self.logger.warning(f"⚠️ Batch {batch_id} completed but {len(failed_customers)} customers failed")

                    self.logger.info(f"✅ Batch {batch_id} completed successfully - {self.completed_batches}/{self.total_batches}")

                    # Send progress update with API response details
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        self.progress_callback({
                            'type': 'batch_success',
                            'batch_id': batch_id,
                            'customers_count': len(batch),
                            'failed_customers_count': len(failed_customers) if failed_customers else 0,
                            'response_data': response_data,
                            'status_code': response.status_code,
                            'response_headers': dict(response.headers),
                            'failed_customers': failed_customers[:5] if failed_customers else []  # Show first 5 failures
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
                        
            # Timeout exception handling removed - API handles its own timeouts
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
        """Save failed batches in format suitable for immediate re-import"""
        if not self.failed_batches:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create retry directory
        retry_dir = f"retry_batches_{timestamp}"
        os.makedirs(retry_dir, exist_ok=True)

        self.logger.info(f"[RETRY] Creating retry files in directory: {retry_dir}")

        # Save each failed batch as a separate importable file
        retry_files = []
        for i, failed_batch in enumerate(self.failed_batches, 1):
            # Create properly formatted batch for re-import
            retry_batch = {
                "data": failed_batch['customers']
            }

            # Generate filename
            retry_filename = f"retry_batch_{i:02d}_failed.json"
            retry_filepath = os.path.join(retry_dir, retry_filename)

            # Save the batch
            with open(retry_filepath, 'w', encoding='utf-8') as f:
                json.dump(retry_batch, f, indent=2, ensure_ascii=False)

            retry_files.append(retry_filename)

            # Log details about this failed batch
            customer_count = len(failed_batch['customers'])
            error_msg = failed_batch.get('error', 'Unknown error')
            self.logger.info(f"[RETRY] {retry_filename}: {customer_count} customers (Error: {error_msg})")

        # Create summary file with error details
        summary_file = os.path.join(retry_dir, "retry_summary.json")
        summary_data = {
            'timestamp': timestamp,
            'total_failed_batches': len(self.failed_batches),
            'total_failed_customers': sum(len(batch['customers']) for batch in self.failed_batches),
            'retry_files': retry_files,
            'error_details': [
                {
                    'batch_id': batch['batch_id'],
                    'customer_count': len(batch['customers']),
                    'error': batch.get('error', 'Unknown error'),
                    'status_code': batch.get('status_code'),
                    'retry_file': f"retry_batch_{i:02d}_failed.json"
                }
                for i, batch in enumerate(self.failed_batches, 1)
            ]
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        # Create instructions file
        instructions_file = os.path.join(retry_dir, "RETRY_INSTRUCTIONS.md")
        instructions_content = f"""# Failed Batch Retry Instructions

## Summary
- **Failed Batches**: {len(self.failed_batches)}
- **Failed Customers**: {sum(len(batch['customers']) for batch in self.failed_batches)}
- **Generated**: {timestamp}

## How to Retry

### Option 1: Use Bulk Import GUI
1. Launch the Bulk Import GUI
2. Go to **Files** tab
3. Click **"Add Directory"**
4. Select this directory: `{retry_dir}`
5. Configure your API credentials
6. Click **"Start Import"**

### Option 2: Use Individual Files
1. Load specific retry files one by one:
{chr(10).join(f'   - {filename}' for filename in retry_files)}

## Error Details
{chr(10).join(f'- **{batch["retry_file"]}**: {batch["customer_count"]} customers - {batch["error"]}' for batch in summary_data["error_details"])}

## Files in this Directory
- `retry_summary.json` - Detailed error information
- `RETRY_INSTRUCTIONS.md` - This file
- `retry_batch_XX_failed.json` - Individual batch files ready for re-import

All retry files are formatted correctly for immediate import!
"""

        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions_content)

        self.logger.info(f"[RETRY] ✅ Created {len(retry_files)} retry files in {retry_dir}")
        self.logger.info(f"[RETRY] 📋 Summary saved to: {summary_file}")
        self.logger.info(f"[RETRY] 📖 Instructions saved to: {instructions_file}")
        self.logger.info(f"[RETRY] 🔄 Ready for immediate re-import!")

        # Notify GUI about retry files creation
        if hasattr(self, 'progress_callback') and self.progress_callback:
            self.progress_callback({
                'type': 'retry_files_created',
                'retry_directory': retry_dir,
                'retry_files': retry_files,
                'failed_batches_count': len(self.failed_batches),
                'failed_customers_count': sum(len(batch['customers']) for batch in self.failed_batches),
                'summary_file': summary_file,
                'instructions_file': instructions_file
            })

# Example usage function
def main():
    # Configuration
    API_URL = "https://prod.cse.cloud4retail.co/customer-profile-service/tenants/001/services/rest/customers-import/v1/customers"
    AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im9hdXRoMi5rZXkuMSJ9..."  # Your full token
    # GK_PASSPORT is now hardcoded in the constructor

    # Initialize importer (GK-Passport is hardcoded)
    importer = BulkCustomerImporter(
        api_url=API_URL,
        auth_token=AUTH_TOKEN,
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