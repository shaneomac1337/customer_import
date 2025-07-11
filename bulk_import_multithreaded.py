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
        
        # API response logging to files
        self.api_responses_dir = "api_responses"
        os.makedirs(self.api_responses_dir, exist_ok=True)
        self.response_file_lock = threading.Lock()

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
        """Parse API response to extract failed customers - ROBUST VERSION"""
        failed_customers = []

        try:
            # Convert response to JSON if it's a string, handle log files gracefully
            if isinstance(response_data, str):
                response_text = response_data
                try:
                    response_json = json.loads(response_data)
                except json.JSONDecodeError:
                    # This might be a log file with multiple JSON blocks, not a single JSON
                    self.logger.debug(f"[PARSE] Response is not valid JSON, treating as log file or raw text")
                    response_json = {"raw_response": response_data}
            else:
                response_json = response_data
                response_text = json.dumps(response_data) if response_data else ""

            self.logger.debug(f"[PARSE] Parsing response for failures. Response keys: {list(response_json.keys()) if isinstance(response_json, dict) else 'Not a dict'}")

            # METHOD 1: Look for customer results in structured data
            customer_results = []

            # Check multiple possible locations for customer data
            possible_data_keys = ['data', 'customers', 'results', 'customerResults']
            for key in possible_data_keys:
                if key in response_json and isinstance(response_json[key], list):
                    customer_results = response_json[key]
                    self.logger.debug(f"[PARSE] Found customer data in '{key}' with {len(customer_results)} entries")
                    break

            # Parse structured customer results
            for customer_result in customer_results:
                if isinstance(customer_result, dict) and customer_result.get('result') in ['FAILED', 'ERROR', 'CONFLICT']:
                    self.logger.info(f"[FAILED] FOUND FAILED CUSTOMER: {customer_result.get('customerId')} - {customer_result.get('username')}")

                    # Find the original customer data
                    customer_id = customer_result.get('customerId')
                    username = customer_result.get('username')

                    # Try to match with original batch data
                    original_customer = None
                    for customer in batch_customers:
                        # Match by card number
                        if customer.get('customerCards') and len(customer['customerCards']) > 0:
                            card_number = customer['customerCards'][0].get('cardNumber')
                            if str(card_number) == str(customer_id):
                                original_customer = customer
                                break

                        # Match by personal number in username
                        if username and customer.get('personalNumber'):
                            personal_num = customer['personalNumber'].replace('-', '')
                            if personal_num in username.replace('-', ''):
                                original_customer = customer
                                break

                    failed_customer = {
                        'customerId': customer_id,
                        'username': username,
                        'result': customer_result.get('result'),
                        'error': customer_result.get('error', customer_result.get('errorMessage', 'Unknown error')),
                        'timestamp': datetime.now().isoformat(),
                        'originalData': original_customer,
                        'batchInfo': f"Found in structured response data"
                    }
                    failed_customers.append(failed_customer)

            # METHOD 2: ENHANCED Fallback - Search raw response text for "FAILED", "ERROR", or "CONFLICT" pattern
            # This handles both single responses and log files with multiple JSON blocks
            if ('"result": "FAILED"' in response_text or '"result":"FAILED"' in response_text or
                '"result": "ERROR"' in response_text or '"result":"ERROR"' in response_text or
                '"result": "CONFLICT"' in response_text or '"result":"CONFLICT"' in response_text):
                self.logger.warning(f"[FALLBACK] Found 'FAILED', 'ERROR', or 'CONFLICT' in raw response text, extracting all failures...")

                # Enhanced regex to extract failed customers from log files or single responses
                import re
                failed_pattern = r'"customerId":\s*"([^"]+)"[^}]*"username":\s*"([^"]+)"[^}]*"result":\s*"(?:FAILED|ERROR|CONFLICT)"'
                matches = re.findall(failed_pattern, response_text)

                self.logger.info(f"[REGEX] Found {len(matches)} failed customer matches in response text")

                for customer_id, username in matches:
                    # Check if we already found this customer via structured parsing
                    already_found = any(fc['customerId'] == customer_id for fc in failed_customers)
                    if not already_found:
                        self.logger.info(f"[REGEX] NEW FAILED CUSTOMER: {customer_id} - {username}")

                        # Try to match with original batch data
                        original_customer = None
                        for customer in batch_customers:
                            if customer.get('customerCards') and len(customer['customerCards']) > 0:
                                card_number = customer['customerCards'][0].get('cardNumber')
                                if str(card_number) == str(customer_id):
                                    original_customer = customer
                                    break

                        failed_customer = {
                            'customerId': customer_id,
                            'username': username,
                            'result': 'FAILED',  # Will be FAILED or ERROR from regex
                            'error': 'Detected via regex fallback - no specific error message',
                            'timestamp': datetime.now().isoformat(),
                            'originalData': original_customer,
                            'batchInfo': f"Found via regex fallback in raw response"
                        }
                        failed_customers.append(failed_customer)
                    else:
                        self.logger.debug(f"[REGEX] DUPLICATE: {customer_id} already found via structured parsing")

            # METHOD 3: Check for other failure indicators
            if 'errors' in response_json and isinstance(response_json['errors'], list):
                for error in response_json['errors']:
                    # Ensure error is a dict before calling .get()
                    if isinstance(error, dict):
                        failed_customer = {
                            'customerId': error.get('customerId', 'Unknown'),
                            'username': error.get('username', 'Unknown'),
                            'result': 'FAILED',
                            'error': error.get('message', error.get('errorMessage', str(error))),
                            'timestamp': datetime.now().isoformat(),
                            'originalData': None,
                            'batchInfo': f"Found in errors array"
                        }
                        failed_customers.append(failed_customer)

            if failed_customers:
                self.logger.warning(f"[FAILED] TOTAL FAILED CUSTOMERS DETECTED: {len(failed_customers)}")
            else:
                self.logger.debug(f"[PARSE] No failed customers detected in this batch")

        except Exception as e:
            self.logger.error(f"❌ Error parsing API response for failures: {e}")
            self.logger.error(f"Response data type: {type(response_data)}")
            if hasattr(response_data, '__len__'):
                self.logger.error(f"Response data length: {len(response_data)}")

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

    def _save_failed_batch(self, batch: List[Dict[Any, Any]], batch_id: int):
        """Save entire batch that contains failed customers to batches_to_retry directory"""
        with self.failed_customers_lock:
            # Create timestamped retry directory to avoid overwriting
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            retry_dir = os.path.join("failed_customers", f"batches_to_retry_{timestamp}")
            os.makedirs(retry_dir, exist_ok=True)

            # Create filename with batch number
            batch_filename = f"batch_{batch_id:03d}.json"
            batch_filepath = os.path.join(retry_dir, batch_filename)

            # Save the batch in the same format as the original API call
            batch_data = {
                "data": batch
            }

            try:
                with open(batch_filepath, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"💾 Saved failed batch {batch_id} to {batch_filepath} ({len(batch)} customers)")
            except Exception as e:
                self.logger.error(f"❌ Error saving failed batch {batch_id}: {e}")

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

                    # Parse response - ROBUST VERSION
                    response_data = {}
                    response_text = ""
                    try:
                        if response.content:
                            response_text = response.text
                            response_data = response.json()
                            self.logger.debug(f"📥 Batch {batch_id} response parsed successfully. Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"⚠️ Batch {batch_id} - JSON decode error: {e}")
                        response_data = {'raw_response': response_text}

                    # ALWAYS check for failed customers within successful response
                    self.logger.info(f"[CHECK] Batch {batch_id} - Checking for failed customers in response...")

                    failed_customers = self._parse_api_response_for_failures(response_data, batch)

                    if failed_customers:
                        self._save_failed_customers(failed_customers)
                        # Save the entire batch for easy retry
                        self._save_failed_batch(batch, batch_id)
                        self.logger.error(f"[FAILED] Batch {batch_id} completed with HTTP 200 but {len(failed_customers)} customers FAILED!")
                        for fc in failed_customers[:3]:  # Show first 3 failures
                            self.logger.error(f"   - Failed: {fc['customerId']} ({fc['username']}) - {fc['error']}")
                        if len(failed_customers) > 3:
                            self.logger.error(f"   - ... and {len(failed_customers) - 3} more failures")
                    else:
                        self.logger.info(f"[SUCCESS] Batch {batch_id} - No failed customers detected")

                    self.logger.info(f"✅ Batch {batch_id} completed successfully - {self.completed_batches}/{self.total_batches}")

                    # Save full API response to file and get summary
                    response_summary = self._save_api_response_to_file(
                        batch_id, response_data, response.status_code, dict(response.headers), "success"
                    )
                    
                    # Create memory-efficient summary for GUI
                    gui_summary = self._create_response_summary_for_gui(response_data, failed_customers)

                    # Send progress update with lightweight data
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        self.progress_callback({
                            'type': 'batch_success',
                            'batch_id': batch_id,
                            'customers_count': len(batch),
                            'failed_customers_count': len(failed_customers) if failed_customers else 0,
                            'response_summary': gui_summary,  # Lightweight summary instead of full data
                            'response_file': response_summary['response_file'],  # File reference
                            'status_code': response.status_code,
                            'response_headers': {  # Only essential headers
                                'content-type': dict(response.headers).get('content-type', 'unknown'),
                                'content-length': dict(response.headers).get('content-length', 'unknown')
                            },
                            'failed_customers': failed_customers[:3] if failed_customers else []  # Only first 3 for GUI
                        })

                    # Save API response to file
                    response_summary = self._save_api_response_to_file(batch_id, response_data, response.status_code, dict(response.headers), response_type="success")
                    
                    return {
                        'batch_id': batch_id,
                        'status': 'success',
                        'customers_count': len(batch),
                        'response': response_data,
                        'status_code': response.status_code,
                        'response_headers': dict(response.headers),
                        'response_file': response_summary.get('response_file'),
                        'data_size': response_summary.get('data_size'),
                        'has_data': response_summary.get('has_data')
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

                    # Save error response to file
                    error_summary = self._save_api_response_to_file(
                        batch_id, error_data, response.status_code, dict(response.headers), "error"
                    )

                    # Send progress update with API error details
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        self.progress_callback({
                            'type': 'batch_error',
                            'batch_id': batch_id,
                            'customers_count': len(batch),
                            'error_summary': error_data.get('error', str(error_data))[:200] if error_data else 'Unknown error',  # Summary only
                            'response_file': error_summary['response_file'],  # File reference
                            'status_code': response.status_code,
                            'response_headers': {  # Essential headers only
                                'content-type': dict(response.headers).get('content-type', 'unknown')
                            },
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

        # This should never be reached, but added for type safety
        return {
            'batch_id': batch_id,
            'status': 'failed',
            'error': 'Unexpected end of method - all retries exhausted'
        }
    
    def import_customers(self, file_paths: List[str]) -> Dict[str, Any]:
        """Import customers from multiple files using multithreading"""
        
        start_time = datetime.now()
        self.logger.info(f"🚀 Starting bulk import from {len(file_paths)} files")
        
        # Create batches from files without loading all into memory
        all_batches = []
        total_customers = 0

        for file_path in file_paths:
            customers = self.load_customer_data(file_path)
            if customers:
                file_batches = self.create_batches(customers)
                all_batches.extend(file_batches)
                total_customers += len(customers)
                self.logger.info(f"Loaded {len(customers)} customers from {file_path} -> {len(file_batches)} batches")
                # Clear customers from memory immediately after creating batches
                del customers
            else:
                self.logger.warning(f"No customers found in {file_path}")

        if not all_batches:
            self.logger.error("No customer data loaded!")
            return {'status': 'error', 'message': 'No customer data loaded'}

        # Use the batches we created
        batches = all_batches
        self.total_batches = len(batches)

        self.logger.info(f"📊 Total customers to import: {total_customers}")
        
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
        
        # Use the total_customers we calculated during loading
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

    def _save_api_response_to_file(self, batch_id: int, response_data: dict, status_code: int, headers: dict, response_type: str = "success"):
        """Save full API response to file and return summary for memory efficiency"""
        try:
            with self.response_file_lock:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"batch_{batch_id:03d}_{response_type}_{timestamp}.json"
                filepath = os.path.join(self.api_responses_dir, filename)
                
                # Full response data for file
                full_response = {
                    'timestamp': timestamp,
                    'batch_id': batch_id,
                    'status_code': status_code,
                    'headers': headers,
                    'response_data': response_data,
                    'response_type': response_type
                }
                
                # Save to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(full_response, f, indent=2, ensure_ascii=False)
                
                self.logger.debug(f"[API_LOG] Saved full response to: {filename}")
                
                # Return lightweight summary for GUI
                summary = {
                    'batch_id': batch_id,
                    'status_code': status_code,
                    'response_file': filename,
                    'data_size': len(str(response_data)) if response_data else 0,
                    'has_data': bool(response_data),
                    'timestamp': timestamp
                }
                
                # Add key response info without full data
                if isinstance(response_data, dict):
                    if 'data' in response_data and isinstance(response_data['data'], list):
                        summary['customers_processed'] = len(response_data['data'])
                    if 'message' in response_data:
                        summary['message'] = response_data['message'][:100]  # First 100 chars
                    if 'error' in response_data:
                        summary['error_summary'] = response_data['error'][:200]  # First 200 chars
                
                return summary
                
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to save API response to file: {e}")
            # Return basic summary even if file save fails
            return {
                'batch_id': batch_id,
                'status_code': status_code,
                'response_file': 'save_failed',
                'data_size': len(str(response_data)) if response_data else 0,
                'error': f"File save failed: {e}"
            }

    def _create_response_summary_for_gui(self, response_data: dict, failed_customers: list):
        """Create memory-efficient summary for GUI display"""
        summary = {}
        
        # Basic response info without full data
        if isinstance(response_data, dict):
            # Count results without storing full data
            if 'data' in response_data and isinstance(response_data['data'], list):
                summary['total_customers'] = len(response_data['data'])
                
                # Count successes/failures without storing details
                success_count = 0
                failure_count = 0
                for customer in response_data['data']:
                    if isinstance(customer, dict):
                        result = customer.get('result', 'SUCCESS')
                        if result in ['FAILED', 'ERROR', 'CONFLICT']:
                            failure_count += 1
                        else:
                            success_count += 1
                
                summary['success_count'] = success_count
                summary['failure_count'] = failure_count
            
            # Include error messages but not full data
            if 'error' in response_data:
                summary['api_error'] = str(response_data['error'])[:200]
            if 'message' in response_data:
                summary['api_message'] = str(response_data['message'])[:100]
        
        # Add failed customer count from our parsing
        summary['parsed_failed_count'] = len(failed_customers) if failed_customers else 0
        
        return summary

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