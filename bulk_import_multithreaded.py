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
import gc
from auth_manager import AuthenticationManager

class BulkCustomerImporter:
    def __init__(self,
                 api_url: str = None,
                 auth_url: str = None,  # Configurable auth URL
                 auth_token: str = None,
                 gk_passport: str = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg==",
                 batch_size: int = 70,
                 max_workers: int = 5,
                 delay_between_requests: float = 1.0,
                 max_retries: int = 3,
                 progress_callback=None,
                 # Authentication mode
                 mode: str = "C4R",  # "C4R" or "Engage"
                 import_type: str = "customers",  # "customers" or "households"
                 # Authentication parameters
                 username: str = None,
                 password: str = None,
                 use_auto_auth: bool = False,
                 client_id: str = None,  # For Engage mode
                 # Failed customers tracking
                 failed_customers_file: str = "failed_customers.json"):

        self.mode = mode.upper()
        self.import_type = import_type.lower()  # "customers" or "households"
        
        # Determine data key based on import type
        self.data_key = "households" if self.import_type == "households" else "data"
        
        # Set API URL default based on mode and import type if not provided
        if api_url is None:
            if self.mode == "C4R":
                if self.import_type == "customers":
                    self.api_url = "https://prod.cse.cloud4retail.co/customer-profile-service/tenants/001/services/rest/customers-import/v1/customers"
                else:
                    self.api_url = "https://prod.cse.cloud4retail.co/customer-profile-service/tenants/001/services/rest/customers-import/v1/households"
            elif self.mode == "ENGAGE":
                if self.import_type == "customers":
                    self.api_url = "https://dev.cse.gk-engage.co/api/customer-profile/services/rest/customers-import/v1/customers"
                else:
                    self.api_url = "https://dev.cse.gk-engage.co/api/customer-profile/services/rest/customers-import/v1/households"
            else:
                raise ValueError(f"Invalid mode: {mode}. Must be 'C4R' or 'Engage'")
        else:
            self.api_url = api_url
            
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
        self.max_retries = max_retries
        self.progress_callback = progress_callback

        # Create failed items directory based on import type
        item_name = "households" if self.import_type == "households" else "customers"
        self.failed_items_dir = f"failed_{item_name}"
        os.makedirs(self.failed_items_dir, exist_ok=True)

        # Set failed items file path in the dedicated folder
        if not os.path.dirname(failed_customers_file):
            # If no directory specified, put it in failed_items folder
            default_filename = f"failed_{item_name}.json"
            self.failed_customers_file = os.path.join(self.failed_items_dir, default_filename)
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
                mode=self.mode,
                username=username,
                password=password,
                gk_passport=gk_passport,
                auth_url=auth_url,  # Pass configurable auth URL
                client_id=client_id
            )
            self.auth_token = None  # Will be managed automatically
            self.gk_passport = gk_passport if self.mode == "C4R" else None
        else:
            # Use manual token (legacy mode)
            self.auth_manager = None
            self.auth_token = auth_token
            self.gk_passport = gk_passport if self.mode == "C4R" else None

        # Authentication monitoring
        self.auth_failures = []
        self.auth_service_down = False
        self.last_auth_check = None
        self.auth_check_interval = 300  # Check auth service every 5 minutes

        # Import control
        self.should_stop = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        self.processed_batches = 0
        self.remaining_batches = []

        # Setup logging FIRST (before any methods that use self.logger)
        # Configure handlers with UTF-8 encoding to handle emoji characters
        file_handler = logging.FileHandler('bulk_import.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Set formatter for both handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        self.logger = logging.getLogger(__name__)

        # Create single_failures directory structure proactively
        self._ensure_single_failures_structure()

    def _ensure_single_failures_structure(self):
        """Create the single_failures directory structure proactively"""
        try:
            single_failures_base = os.path.join(self.failed_items_dir, "single_failures")
            os.makedirs(single_failures_base, exist_ok=True)

            # Create README if it doesn't exist
            readme_path = os.path.join(single_failures_base, "README.md")
            if not os.path.exists(readme_path):
                readme_content = """# Single Failures Directory Structure

This directory will contain individual failed customers organized by failure reason when imports have failures.

## Directory Structure (Created Automatically):
```
single_failures/
├── CONFLICT/          # Customers that failed due to conflicts (duplicates, etc.)
├── FAILED/            # Customers that failed due to validation or business logic
├── ERROR/             # Customers that failed due to system errors
└── UNKNOWN/           # Customers with unrecognized failure reasons
```

**Note**: Directories are created automatically when customers fail during import.

## File Types:
- **customer_*.json** - Individual customer files in direct import format
- **_SUMMARY_*.json** - Summary files with overview of each failure type

## How to Use:
1. **Individual Retry**: Use any customer_*.json file to retry a single customer
2. **Batch Retry**: Collect multiple customers and create a batch for retry
3. **Analysis**: Use summary files to understand failure patterns

## File Format:
Each customer file is in **clean import format** (identical to retry batches):
```json
{
  "data": [
    {
      // Complete customer data ready for import
    }
  ]
}
```

**Ready for Direct Import**: Just drag and drop any customer_*.json file into the import tool!

## Auto-Generated:
These folders and files are automatically created when customers fail during import.
The structure helps organize failures by type for easier handling and retry.
"""
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                self.logger.info(f"Created single_failures directory structure with README")

            # Structure is ready (either existed or just created)

        except Exception as e:
            self.logger.error(f"Could not create single_failures structure: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

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

    def check_auth_service_health(self) -> Dict[str, Any]:
        """Check if authentication service is healthy"""
        if not self.auth_manager:
            return {'healthy': True, 'message': 'Manual auth mode - no service check needed'}

        try:
            # Test authentication to check service health
            result = self.auth_manager.test_authentication()

            if result['success']:
                self.auth_service_down = False
                self.last_auth_check = datetime.now()
                return {
                    'healthy': True,
                    'message': 'Auth service is healthy',
                    'response_time_ms': result.get('response_time_ms', 0)
                }
            else:
                # Check if it's a service down error (503, 502, 504)
                error_msg = result.get('error', '').lower()
                if any(code in error_msg for code in ['503', '502', '504', 'service unavailable', 'bad gateway', 'timeout']):
                    self.auth_service_down = True
                    self.logger.error(f"[AUTH SERVICE DOWN] {result.get('error')}")
                    return {
                        'healthy': False,
                        'service_down': True,
                        'message': f"Auth service is down: {result.get('error')}",
                        'error': result.get('error')
                    }
                else:
                    return {
                        'healthy': False,
                        'service_down': False,
                        'message': f"Auth service error: {result.get('error')}",
                        'error': result.get('error')
                    }

        except Exception as e:
            self.auth_service_down = True
            self.logger.error(f"[AUTH SERVICE CHECK FAILED] {e}")
            return {
                'healthy': False,
                'service_down': True,
                'message': f"Auth service check failed: {e}",
                'error': str(e)
            }

    def should_check_auth_service(self) -> bool:
        """Check if we should perform an auth service health check"""
        if not self.auth_manager:
            return False

        if not self.last_auth_check:
            return True

        time_since_check = (datetime.now() - self.last_auth_check).total_seconds()
        return time_since_check >= self.auth_check_interval

    def stop_import(self):
        """Stop the import process gracefully"""
        self.should_stop = True
        self.logger.info("[STOP] STOP REQUESTED - Import will stop after current batches complete")

    def pause_import(self):
        """Pause the import process"""
        self.is_paused = True
        self.pause_event.clear()
        self.logger.info("⏸️ PAUSE REQUESTED - Import will pause after current batches complete")

    def resume_import(self):
        """Resume the paused import process"""
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.logger.info("▶️ RESUME REQUESTED - Import will continue")

    def get_import_status(self) -> Dict[str, Any]:
        """Get current import status"""
        return {
            'should_stop': self.should_stop,
            'is_paused': self.is_paused,
            'processed_batches': self.processed_batches,
            'remaining_batches': len(self.remaining_batches),
            'auth_service_down': self.auth_service_down
        }
    
    def load_customer_data(self, file_path: str) -> List[Dict[Any, Any]]:
        """Load customer/household data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(self.data_key, [])
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

    def load_lazy_batch(self, lazy_batch_info: Dict[str, Any]) -> List[Dict[Any, Any]]:
        """Load a specific batch from file using lazy batch info"""
        try:
            file_path = lazy_batch_info['file_path']
            start_idx = lazy_batch_info['start_idx']
            end_idx = lazy_batch_info['end_idx']

            # Load only the items we need for this batch (customers or households)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_items = data.get(self.data_key, [])

                # Extract only the slice we need
                batch_items = all_items[start_idx:end_idx]
                return batch_items

        except Exception as e:
            self.logger.error(f"Error loading lazy batch from {lazy_batch_info.get('file_path', 'unknown')}: {e}")
            return []

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
                # Check if result is not a success type (catch any failure)
                result = customer_result.get('result', '').upper() if isinstance(customer_result, dict) else ''
                if result and result not in ['SUCCESS', 'OK', 'IMPORTED', 'ACCEPTED']:
                    self.logger.info(f"[FAILED] FOUND FAILED CUSTOMER: {customer_result.get('customerId')} - {customer_result.get('username')} - Result: {result}")

                    # Find the original customer data
                    customer_id = customer_result.get('customerId')
                    username = customer_result.get('username')

                    # Try to match with original batch data
                    original_customer = None
                    
                    # Skip matching if ID is None/null
                    if customer_id is not None:
                        for customer in batch_customers:
                            # For households: check householdId directly
                            if self.import_type == "households":
                                if customer.get('householdId') == str(customer_id):
                                    original_customer = customer
                                    break
                            else:
                                # For customers: Handle nested person structure
                                person_data = customer.get('person', customer)

                                # Match by customer ID directly
                                if person_data.get('customerId') == str(customer_id):
                                    original_customer = customer
                                    break

                                # Match by card number (check both 'number' and 'cardNumber' fields)
                                if person_data.get('customerCards') and len(person_data['customerCards']) > 0:
                                    card_data = person_data['customerCards'][0]
                                    card_number = card_data.get('number') or card_data.get('cardNumber')
                                    if card_number and str(card_number) == str(customer_id):
                                        original_customer = customer
                                        break

                                # Match by personal number in username
                                if username and person_data.get('personalNumber'):
                                    personal_num = person_data['personalNumber'].replace('-', '')
                                    if personal_num in username.replace('-', ''):
                                        original_customer = customer
                                        break
                    
                    # FALLBACK 1: If no match found and batch has only 1 item, assume it's the failed one
                    if original_customer is None and len(batch_customers) == 1:
                        original_customer = batch_customers[0]
                        self.logger.warning(f"[FALLBACK] Could not match failed item by ID (ID was {customer_id}), but batch has only 1 item - assuming match")
                    
                    # FALLBACK 2: If ALL items failed and we're processing them in order, match by position
                    # This handles the case where API returns failures without IDs
                    if original_customer is None and len(customer_results) == len(batch_customers):
                        # Calculate which position this failure is at
                        failure_index = customer_results.index(customer_result)
                        if failure_index < len(batch_customers):
                            original_customer = batch_customers[failure_index]
                            self.logger.warning(f"[FALLBACK] All {len(customer_results)} items failed - matching by position {failure_index}")

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
                failed_pattern = r'"customerId":\s*"([^"]+)"[^}]*"username":\s*"([^"]+)"[^}]*"result":\s*"(FAILED|ERROR|CONFLICT)"'
                matches = re.findall(failed_pattern, response_text)

                self.logger.info(f"[REGEX] Found {len(matches)} failed customer matches in response text")

                for customer_id, username, result_type in matches:
                    # Check if we already found this customer via structured parsing
                    already_found = any(fc['customerId'] == customer_id for fc in failed_customers)
                    if not already_found:
                        self.logger.info(f"[REGEX] NEW FAILED CUSTOMER: {customer_id} - {username}")

                        # Try to match with original batch data
                        original_customer = None
                        
                        # Skip matching if ID is None/null
                        if customer_id is not None:
                            for customer in batch_customers:
                                # For households: check householdId directly
                                if self.import_type == "households":
                                    if customer.get('householdId') == str(customer_id):
                                        original_customer = customer
                                        break
                                else:
                                    # For customers: Handle nested person structure
                                    person_data = customer.get('person', customer)

                                    # Match by customer ID directly
                                    if person_data.get('customerId') == str(customer_id):
                                        original_customer = customer
                                        break

                                    # Match by card number (check both 'number' and 'cardNumber' fields)
                                    if person_data.get('customerCards') and len(person_data['customerCards']) > 0:
                                        card_data = person_data['customerCards'][0]
                                        card_number = card_data.get('number') or card_data.get('cardNumber')
                                        if card_number and str(card_number) == str(customer_id):
                                            original_customer = customer
                                            break

                                    # Match by username pattern (firstName lastName-personalNumber)
                                    if username and person_data.get('firstName') and person_data.get('lastName'):
                                        expected_username_start = f"{person_data['firstName']} {person_data['lastName']}"
                                        if username.upper().startswith(expected_username_start.upper().replace(' ', ' ')):
                                            original_customer = customer
                                            break
                        
                        # FALLBACK: If no match found and batch has only 1 item, assume it's the failed one
                        if original_customer is None and len(batch_customers) == 1:
                            original_customer = batch_customers[0]
                            self.logger.warning(f"[FALLBACK] Could not match failed item by ID (ID was {customer_id}), but batch has only 1 item - assuming match")

                        failed_customer = {
                            'customerId': customer_id,
                            'username': username,
                            'result': result_type,  # Use the captured result type (FAILED, ERROR, or CONFLICT)
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
                item_name = "households" if self.import_type == "households" else "customers"
                self.logger.warning(f"[FAILED] TOTAL FAILED {item_name.upper()} DETECTED: {len(failed_customers)}")
            else:
                item_name = "households" if self.import_type == "households" else "customers"
                self.logger.debug(f"[PARSE] No failed {item_name} detected in this batch")

        except Exception as e:
            self.logger.error(f"[ERROR] Error parsing API response for failures: {e}")
            self.logger.error(f"Response data type: {type(response_data)}")
            if hasattr(response_data, '__len__'):
                self.logger.error(f"Response data length: {len(response_data)}")

        return failed_customers

    def _save_failed_customers(self, failed_customers):
        """Save failed customers to file and organize by failure reason"""
        if not failed_customers:
            return

        with self.failed_customers_lock:
            self.failed_customers.extend(failed_customers)

            # Save to main file (existing functionality)
            try:
                with open(self.failed_customers_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_customers, f, indent=2, ensure_ascii=False)
                logging.info(f"Saved {len(failed_customers)} failed customers to {self.failed_customers_file}")
            except Exception as e:
                logging.error(f"Error saving failed customers to file: {e}")

            # NEW: Save individual customers organized by failure reason
            self._save_individual_failed_customers_by_reason(failed_customers)

    def _save_individual_failed_customers_by_reason(self, failed_customers: List[Dict[str, Any]]):
        """Save individual failed items (customers/households) organized by failure reason (CONFLICT, FAILED, ERROR)"""
        if not failed_customers:
            return

        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get terminology based on import type
            item_name = "households" if self.import_type == "households" else "customers"
            item_name_single = "household" if self.import_type == "households" else "customer"

            # Group items by failure reason dynamically
            customers_by_reason = {}

            for customer in failed_customers:
                result = customer.get('result', 'UNKNOWN').upper()
                # Use 'UNKNOWN' if result is empty or None
                if not result or result == 'NONE':
                    result = 'UNKNOWN'
                
                # Dynamically create folder for this result type
                if result not in customers_by_reason:
                    customers_by_reason[result] = []
                
                customers_by_reason[result].append(customer)

            # Save each group to separate folders
            for reason, customers in customers_by_reason.items():
                if not customers:  # Skip empty groups
                    continue

                # Create directory structure: failed_items/single_failures/REASON
                base_single_failures_dir = os.path.join(f"failed_{item_name}", "single_failures")
                reason_dir = os.path.join(base_single_failures_dir, reason)
                os.makedirs(reason_dir, exist_ok=True)

                # Save each item as individual file
                saved_count = 0
                for i, customer in enumerate(customers, 1):
                    # Try to get ID from API response first
                    customer_id = customer.get('customerId', f'unknown_{i}')
                    username = customer.get('username', f'unknown_user_{i}')
                    
                    # If API response doesn't have ID, try to extract from originalData
                    original_data = customer.get('originalData')
                    if original_data and (not customer_id or customer_id == 'None' or str(customer_id) == 'None'):
                        # For households: get householdId
                        if self.import_type == "households":
                            customer_id = original_data.get('householdId', f'item{i:05d}')
                        else:
                            # For customers: get customerId from person data
                            person_data = original_data.get('person', original_data)
                            customer_id = person_data.get('customerId', f'item{i:05d}')
                            # Also try to get a better username from person data
                            if not username or username == 'None':
                                first_name = person_data.get('firstName', '')
                                last_name = person_data.get('lastName', '')
                                if first_name or last_name:
                                    username = f"{first_name}_{last_name}".strip('_')

                    # Create safe filename (remove invalid characters)
                    safe_customer_id = "".join(c for c in str(customer_id) if c.isalnum() or c in ('-', '_'))
                    safe_username = "".join(c for c in str(username) if c.isalnum() or c in ('-', '_'))
                    
                    # If both ID and username are still empty/None, add counter to make filename unique
                    if not safe_customer_id or safe_customer_id == 'None':
                        safe_customer_id = f'item{i:05d}'
                    if not safe_username or safe_username == 'None':
                        safe_username = f'unknown'

                    # For households, skip username in filename (not relevant)
                    if self.import_type == "households":
                        item_filename = f"{item_name_single}_{safe_customer_id}.json"
                    else:
                        item_filename = f"{item_name_single}_{safe_customer_id}_{safe_username}.json"
                    
                    item_filepath = os.path.join(reason_dir, item_filename)

                    # Prepare item data in direct import format (exactly like retry batches)
                    original_data = customer.get('originalData')
                    
                    if original_data:
                        # Format exactly like retry batches - use correct data key
                        item_data = {
                            self.data_key: [original_data]
                        }
                        
                        # Save individual item file
                        with open(item_filepath, 'w', encoding='utf-8') as f:
                            json.dump(item_data, f, indent=2, ensure_ascii=False)
                        
                        saved_count += 1
                    else:
                        # Skip items without original data
                        self.logger.warning(f"Skipping {item_name_single} {customer.get('customerId', 'Unknown')} - no original data available for retry")
                        continue

                self.logger.info(f"[INDIVIDUAL {item_name.upper()}] Saved {saved_count}/{len(customers)} {reason} {item_name} to {reason_dir}")

                # Create summary file for this failure reason
                summary_filepath = os.path.join(reason_dir, f"_SUMMARY_{reason}.json")
                summary_data = {
                    "import_type": self.import_type,
                    "failure_reason": reason,
                    f"total_{item_name}": len(customers),
                    "timestamp": timestamp,
                    "directory": reason_dir,
                    "directory_structure": f"failed_{item_name}/single_failures/{reason}",
                    f"{item_name}_list": [
                        {
                            "customerId": c.get('customerId'),
                            "username": c.get('username'),
                            "error": c.get('error', 'No error message')[:100]  # Truncate long errors
                        }
                        for c in customers
                    ]
                }

                with open(summary_filepath, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"[ERROR] Error saving individual failed customers by reason: {e}")

    def _save_failed_batch(self, batch: List[Dict[Any, Any]], batch_id: int):
        """Save entire batch that contains failed items to batches_to_retry directory"""
        with self.failed_customers_lock:
            # Create timestamped retry directory to avoid overwriting
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            retry_dir = os.path.join(self.failed_items_dir, f"batches_to_retry_{timestamp}")
            os.makedirs(retry_dir, exist_ok=True)

            # Create filename with batch number (5 digits for 50K+ files)
            batch_filename = f"batch_{batch_id:05d}.json"
            batch_filepath = os.path.join(retry_dir, batch_filename)

            # Save the batch in the same format as the original API call using correct data key
            batch_data = {
                self.data_key: batch
            }

            try:
                with open(batch_filepath, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"[SAVE] Saved failed batch {batch_id} to {batch_filepath} ({len(batch)} customers)")
            except Exception as e:
                self.logger.error(f"[ERROR] Error saving failed batch {batch_id}: {e}")

    def _save_response_nok_batch(self, batch: List[Dict[Any, Any]], batch_id: int, status_code: int, response_text: str):
        """Save batch that failed with non-200 HTTP response to response_nok directory"""
        with self.failed_customers_lock:
            # Create timestamped response_nok directory
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            response_nok_dir = os.path.join(self.failed_items_dir, f"response_nok_{timestamp}")
            os.makedirs(response_nok_dir, exist_ok=True)

            # Create filename with batch number and status code (5 digits for 50K+ files)
            batch_filename = f"batch_{batch_id:05d}_status_{status_code}.json"
            batch_filepath = os.path.join(response_nok_dir, batch_filename)

            # Save the batch in the same format as the original API call using correct data key
            batch_data = {
                self.data_key: batch,
                "error_info": {
                    "batch_id": batch_id,
                    "status_code": status_code,
                    "response_text": response_text[:500],  # Limit response text length
                    "timestamp": datetime.now().isoformat(),
                    "customer_count": len(batch)
                }
            }

            try:
                with open(batch_filepath, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"[RESPONSE_NOK] Saved non-200 batch {batch_id} (HTTP {status_code}) to {batch_filepath}")
            except Exception as e:
                self.logger.error(f"[ERROR] Error saving response_nok batch {batch_id}: {e}")

    def _save_auth_service_failure_batch(self, batch: List[Dict[Any, Any]], batch_id: int, error_message: str):
        """Save batch that failed due to auth service being down to auth_service_down directory"""
        with self.failed_customers_lock:
            # Create timestamped auth_service_down directory
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auth_down_dir = os.path.join(self.failed_items_dir, f"auth_service_down_{timestamp}")
            os.makedirs(auth_down_dir, exist_ok=True)

            # Create filename with batch number
            batch_filename = f"batch_{batch_id:05d}_auth_service_down.json"
            batch_filepath = os.path.join(auth_down_dir, batch_filename)

            # Save the batch with auth service error info using correct data key
            batch_data = {
                self.data_key: batch,
                "auth_service_error": {
                    "batch_id": batch_id,
                    "error_message": error_message,
                    "timestamp": datetime.now().isoformat(),
                    "customer_count": len(batch),
                    "error_type": "auth_service_down",
                    "retry_instructions": "Wait for auth service to be restored, then retry this batch"
                }
            }

            try:
                with open(batch_filepath, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, indent=2, ensure_ascii=False)
                self.logger.error(f"[AUTH_SERVICE_DOWN] Saved batch {batch_id} to {batch_filepath}")
            except Exception as e:
                self.logger.error(f"[ERROR] Error saving auth service failure batch {batch_id}: {e}")

    def save_remaining_work(self, reason: str = "stopped"):
        """Save remaining work for resume functionality"""
        if not self.remaining_batches:
            return None

        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resume_dir = os.path.join(self.failed_items_dir, f"resume_work_{timestamp}")
            os.makedirs(resume_dir, exist_ok=True)

            # Save remaining batch info
            resume_filename = f"remaining_batches_{reason}.json"
            resume_filepath = os.path.join(resume_dir, resume_filename)

            resume_data = {
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "processed_batches": self.processed_batches,
                "total_batches": self.total_batches,
                "remaining_batches": self.remaining_batches,
                "auth_service_down": self.auth_service_down,
                "resume_instructions": "Use this file to resume the import from where it left off"
            }

            with open(resume_filepath, 'w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"[SAVE] SAVED REMAINING WORK: {len(self.remaining_batches)} batches saved to {resume_filepath}")
            return resume_filepath

        except Exception as e:
            self.logger.error(f"[ERROR] Error saving remaining work: {e}")
            return None

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

        # Check auth service health periodically
        if self.should_check_auth_service():
            health_check = self.check_auth_service_health()
            if not health_check['healthy'] and health_check.get('service_down'):
                self.logger.error(f"[AUTH SERVICE DOWN] Aborting batch {batch_id}")
                # Save this as an auth service failure
                self._save_auth_service_failure_batch(batch, batch_id, health_check['error'])
                return {
                    'batch_id': batch_id,
                    'status': 'failed',
                    'error': f'Auth service down: {health_check["error"]}',
                    'error_type': 'auth_service_down'
                }

        # Get authentication headers (with automatic refresh if needed)
        if self.auth_manager:
            try:
                headers = self.auth_manager.get_auth_headers()
            except Exception as e:
                self.logger.error(f"[ERROR] Authentication failed for batch {batch_id}: {e}")

                # Check if this is an auth service down error
                error_msg = str(e).lower()
                if any(code in error_msg for code in ['503', '502', '504', 'service unavailable', 'bad gateway']):
                    self.auth_service_down = True
                    self._save_auth_service_failure_batch(batch, batch_id, str(e))
                    return {
                        'batch_id': batch_id,
                        'status': 'failed',
                        'error': f'Auth service down: {e}',
                        'error_type': 'auth_service_down'
                    }
                else:
                    return {
                        'batch_id': batch_id,
                        'status': 'failed',
                        'error': f'Authentication failed: {e}',
                        'error_type': 'auth_failed'
                    }
        else:
            # Legacy manual token mode
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'GK-Passport': self.gk_passport,
                'Content-Type': 'application/json'
            }
        
        # Use the correct data key based on import type (data for customers, households for households)
        payload = {self.data_key: batch}

        item_name = "households" if self.import_type == "households" else "customers"
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Sending batch {batch_id} (attempt {attempt + 1}/{self.max_retries}) - {len(batch)} {item_name}")
                
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

                    # ALWAYS check for failed items within successful response
                    self.logger.info(f"[CHECK] Batch {batch_id} - Checking for failed {item_name} in response...")

                    failed_customers = self._parse_api_response_for_failures(response_data, batch)

                    if failed_customers:
                        self._save_failed_customers(failed_customers)
                        # Save the entire batch for easy retry
                        self._save_failed_batch(batch, batch_id)
                        self.logger.error(f"[FAILED] Batch {batch_id} completed with HTTP 200 but {len(failed_customers)} {item_name} FAILED!")
                        for fc in failed_customers[:3]:  # Show first 3 failures
                            self.logger.error(f"   - Failed: {fc['customerId']} ({fc['username']}) - {fc['error']}")
                        if len(failed_customers) > 3:
                            self.logger.error(f"   - ... and {len(failed_customers) - 3} more failures")
                    else:
                        self.logger.info(f"[SUCCESS] Batch {batch_id} - No failed {item_name} detected")

                    self.logger.info(f"[SUCCESS] Batch {batch_id} completed successfully - {self.completed_batches}/{self.total_batches}")

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

                        # Save non-200 response batch to response_nok folder
                        self._save_response_nok_batch(batch, batch_id, response.status_code, response.text)
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
                self.logger.error(f"[ERROR] Batch {batch_id} error (attempt {attempt + 1}): {e}")
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

    def send_lazy_batch(self, lazy_batch_info: Dict[str, Any], batch_id: int) -> Dict[str, Any]:
        """Load and send a lazy batch to the API - MEMORY EFFICIENT WITH STOP/PAUSE SUPPORT"""
        batch = None
        try:
            # Check if we should stop before processing
            if self.should_stop:
                self.logger.info(f"[STOP] STOPPING - Batch {batch_id} not processed due to stop request")
                return {
                    'batch_id': batch_id,
                    'status': 'stopped',
                    'error': 'Import stopped by user request'
                }

            # Wait if paused
            if self.is_paused:
                self.logger.info(f"[PAUSE] PAUSED - Batch {batch_id} waiting for resume...")
                self.pause_event.wait()  # Block until resumed

                # Check if stop was requested while paused
                if self.should_stop:
                    self.logger.info(f"[STOP] STOPPING - Batch {batch_id} not processed (stopped while paused)")
                    return {
                        'batch_id': batch_id,
                        'status': 'stopped',
                        'error': 'Import stopped while paused'
                    }

                self.logger.info(f"▶️ RESUMED - Batch {batch_id} continuing...")

            # Load the actual batch data just-in-time
            batch = self.load_lazy_batch(lazy_batch_info)
            if not batch:
                return {
                    'batch_id': batch_id,
                    'status': 'failed',
                    'error': 'Failed to load batch data from file'
                }

            # Log that we're loading this batch
            self.logger.info(f"Loading batch {batch_id} from {lazy_batch_info['file_path']} (customers {lazy_batch_info['start_idx']}-{lazy_batch_info['end_idx']}) - {len(batch)} customers")

            # Send the batch using existing method
            result = self.send_batch(batch, batch_id)

            # Update processed count
            self.processed_batches += 1

            # Explicitly free batch memory immediately after sending
            del batch
            batch = None

            return result

        except Exception as e:
            self.logger.error(f"Error processing lazy batch {batch_id}: {e}")
            return {
                'batch_id': batch_id,
                'status': 'failed',
                'error': str(e)
            }
        finally:
            # Ensure batch is always freed, even on exception
            if batch is not None:
                del batch
    
    def import_customers(self, file_paths: List[str]) -> Dict[str, Any]:
        """Import customers from multiple files using multithreading - TRUE LAZY LOADING"""

        start_time = datetime.now()
        self.logger.info(f"[IMPORT] Starting bulk import from {len(file_paths)} files")

        # Create lazy batch references without loading any data
        lazy_batches = []
        total_customers = 0

        for file_path in file_paths:
            # Only count items, don't load them yet
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    customers_count = len(data.get(self.data_key, []))

                if customers_count > 0:
                    # Calculate how many batches this file will create
                    num_batches = (customers_count + self.batch_size - 1) // self.batch_size

                    # Create lazy batch references
                    for batch_index in range(num_batches):
                        start_idx = batch_index * self.batch_size
                        end_idx = min(start_idx + self.batch_size, customers_count)

                        lazy_batches.append({
                            'file_path': file_path,
                            'start_idx': start_idx,
                            'end_idx': end_idx,
                            'expected_size': end_idx - start_idx
                        })

                    total_customers += customers_count
                    item_name = "households" if self.import_type == "households" else "customers"
                    self.logger.info(f"Planned {customers_count} {item_name} from {file_path} -> {num_batches} batches (not loaded yet)")
                else:
                    item_name = "households" if self.import_type == "households" else "customers"
                    self.logger.warning(f"No {item_name} found in {file_path}")

            except Exception as e:
                self.logger.error(f"Error reading file {file_path}: {e}")

        if not lazy_batches:
            item_name = "household" if self.import_type == "households" else "customer"
            self.logger.error(f"No {item_name} data found!")
            return {'status': 'error', 'message': f'No {item_name} data found'}

        self.total_batches = len(lazy_batches)
        self.remaining_batches = lazy_batches.copy()  # Track remaining work
        item_name = "households" if self.import_type == "households" else "customers"
        self.logger.info(f"[STATS] Total {item_name} to import: {total_customers}")
        self.logger.info(f"[STATS] Planned {len(lazy_batches)} batches (lazy loading - files will be loaded during processing)")

        self.logger.info(f"[STATS] Created {self.total_batches} batches of {self.batch_size} {item_name} each")
        self.logger.info(f"[STATS] Using {self.max_workers} worker threads")
        
        # Process lazy batches with thread pool
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all lazy batches
            future_to_batch = {
                executor.submit(self.send_lazy_batch, lazy_batch, i): i
                for i, lazy_batch in enumerate(lazy_batches, 1)
            }
            
            # Process completed batches with memory cleanup
            stopped_batches = []
            for future in as_completed(future_to_batch):
                batch_id = future_to_batch[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Track stopped batches for resume functionality
                    if result.get('status') == 'stopped':
                        stopped_batches.append(batch_id)
                        self.logger.info(f"[STOP] Batch {batch_id} stopped - can be resumed later")
                    else:
                        # Remove from remaining batches (completed or failed)
                        self.remaining_batches = [b for b in self.remaining_batches if lazy_batches[batch_id-1] != b]

                    # Log memory-efficient completion
                    status = result.get('status', 'unknown')
                    customers_count = result.get('customers_count', 0)
                    item_name = "households" if self.import_type == "households" else "customers"
                    self.logger.debug(f"[COMPLETE] Batch {batch_id} completed ({status}) - {customers_count} {item_name} processed and freed from memory")

                except Exception as e:
                    self.logger.error(f"[ERROR] Batch {batch_id} failed with exception: {e}")
                    results.append({
                        'batch_id': batch_id,
                        'status': 'failed',
                        'error': str(e)
                    })
                finally:
                    # Clean up future reference to help garbage collection
                    future_to_batch.pop(future, None)

                    # Trigger garbage collection every 10 batches to free memory
                    if batch_id % 10 == 0:
                        gc.collect()
                        self.logger.debug(f"[CLEANUP] Memory cleanup triggered after batch {batch_id}")

                    # Check if we should auto-pause due to auth service issues
                    if self.auth_service_down and not self.is_paused and not self.should_stop:
                        self.logger.error("[ALERT] AUTO-PAUSING due to auth service being down")
                        self.pause_import()
        
        # Calculate final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        successful_batches = len([r for r in results if r.get('status') == 'success'])
        failed_batches = len([r for r in results if r.get('status') == 'failed'])
        stopped_batches = len([r for r in results if r.get('status') == 'stopped'])

        # Calculate actual customer counts from results
        successful_customers = sum(r.get('customers_count', 0) for r in results if r.get('status') == 'success')
        failed_customers_count = sum(r.get('customers_count', 0) for r in results if r.get('status') == 'failed')
        stopped_customers_count = sum(lazy_batches[r['batch_id']-1]['expected_size'] for r in results if r.get('status') == 'stopped')
        
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
            'failed_customers': failed_customers_count,
            'success_rate': f"{(successful_customers/total_customers)*100:.1f}%" if total_customers > 0 else '0.0%'
        }
        
        item_name = "households" if self.import_type == "households" else "customers"
        self.logger.info("[SUMMARY] IMPORT SUMMARY:")
        self.logger.info(f"   Total {item_name}: {total_customers}")
        self.logger.info(f"   Successful: {successful_customers}")
        self.logger.info(f"   Failed: {failed_customers_count}")
        if stopped_batches > 0:
            self.logger.info(f"   Stopped: {stopped_customers_count}")
        self.logger.info(f"   Success rate: {summary['success_rate']}")
        self.logger.info(f"   Duration: {duration}")

        # Handle stopped import
        if stopped_batches > 0 or self.should_stop:
            if self.should_stop:
                reason = "user_stop"
                self.logger.info("[STOP] IMPORT STOPPED by user request")
            elif self.auth_service_down:
                reason = "auth_service_down"
                self.logger.info("[STOP] IMPORT STOPPED due to auth service issues")
            else:
                reason = "unknown"
                self.logger.info("[STOP] IMPORT STOPPED for unknown reason")

            # Save remaining work for resume
            resume_file = self.save_remaining_work(reason)
            if resume_file:
                self.logger.info(f"[SAVE] Remaining work saved to: {resume_file}")
                self.logger.info("   Use this file to resume the import later")

        # Check for auth service issues
        if self.auth_service_down:
            self.logger.error("[AUTH SERVICE DOWN] AUTH SERVICE WAS DOWN during import!")
            self.logger.error("   Some failures may be due to auth service issues")
            self.logger.error("   Check auth_service_down_* directories for affected batches")

        # Categorize failures by type
        auth_failures = len([r for r in results if r.get('error_type') == 'auth_service_down'])
        api_failures = failed_batches - auth_failures

        if auth_failures > 0:
            self.logger.error(f"   Auth service failures: {auth_failures} batches")
        if api_failures > 0:
            self.logger.error(f"   API failures: {api_failures} batches")

        # Show individual item failure breakdown
        if self.failed_customers:
            item_name = "households" if self.import_type == "households" else "customers"
            conflict_count = len([c for c in self.failed_customers if c.get('result', '').upper() == 'CONFLICT'])
            failed_count = len([c for c in self.failed_customers if c.get('result', '').upper() == 'FAILED'])
            error_count = len([c for c in self.failed_customers if c.get('result', '').upper() == 'ERROR'])
            unknown_count = len(self.failed_customers) - conflict_count - failed_count - error_count

            self.logger.info(f"[FAILURES] INDIVIDUAL {item_name.upper()} FAILURES:")
            if conflict_count > 0:
                self.logger.info(f"   CONFLICT {item_name}: {conflict_count}")
            if failed_count > 0:
                self.logger.info(f"   FAILED {item_name}: {failed_count}")
            if error_count > 0:
                self.logger.info(f"   ERROR {item_name}: {error_count}")
            if unknown_count > 0:
                self.logger.info(f"   UNKNOWN reason {item_name}: {unknown_count}")
            self.logger.info(f"   Individual {item_name} files saved in failed_{item_name}/single_failures/* directories")

        # Save failed batches for retry
        if self.failed_batches:
            self.save_failed_batches()
        
        return summary
    
    def save_failed_batches(self):
        """Save failed batches in format suitable for immediate re-import"""
        if not self.failed_batches:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get item terminology based on import type
        item_name = "households" if self.import_type == "households" else "customers"
        item_name_single = "household" if self.import_type == "households" else "customer"

        # Create retry directory
        retry_dir = f"retry_batches_{timestamp}"
        os.makedirs(retry_dir, exist_ok=True)

        self.logger.info(f"[RETRY] Creating retry files in directory: {retry_dir}")

        # Save each failed batch as a separate importable file
        retry_files = []
        for i, failed_batch in enumerate(self.failed_batches, 1):
            # Create properly formatted batch for re-import using the correct data key
            retry_batch = {
                self.data_key: failed_batch['customers']  # 'customers' is generic batch items storage
            }

            # Generate filename (5 digits for 50K+ files)
            retry_filename = f"retry_batch_{i:05d}_failed.json"
            retry_filepath = os.path.join(retry_dir, retry_filename)

            # Save the batch
            with open(retry_filepath, 'w', encoding='utf-8') as f:
                json.dump(retry_batch, f, indent=2, ensure_ascii=False)

            retry_files.append(retry_filename)

            # Log details about this failed batch
            item_count = len(failed_batch['customers'])
            error_msg = failed_batch.get('error', 'Unknown error')
            self.logger.info(f"[RETRY] {retry_filename}: {item_count} {item_name} (Error: {error_msg})")

        # Create summary file with error details
        summary_file = os.path.join(retry_dir, "retry_summary.json")
        total_failed_items = sum(len(batch['customers']) for batch in self.failed_batches)
        summary_data = {
            'timestamp': timestamp,
            'import_type': self.import_type,
            'total_failed_batches': len(self.failed_batches),
            f'total_failed_{item_name}': total_failed_items,
            'retry_files': retry_files,
            'error_details': [
                {
                    'batch_id': batch['batch_id'],
                    f'{item_name_single}_count': len(batch['customers']),
                    'error': batch.get('error', 'Unknown error'),
                    'status_code': batch.get('status_code'),
                    'retry_file': f"retry_batch_{i:05d}_failed.json"
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
- **Import Type**: {self.import_type.title()}
- **Failed Batches**: {len(self.failed_batches)}
- **Failed {item_name.title()}**: {total_failed_items}
- **Generated**: {timestamp}

## How to Retry

### Option 1: Use Bulk Import GUI
1. Launch the Bulk Import GUI
2. Go to **Files** tab
3. Click **"Add Directory"**
4. Select this directory: `{retry_dir}`
5. Set Import Type to **{self.import_type.title()}**
6. Configure your API credentials
7. Click **"Start Import"**

### Option 2: Use Individual Files
1. Load specific retry files one by one:
{chr(10).join(f'   - {filename}' for filename in retry_files)}

## Error Details
{chr(10).join(f'- **{batch["retry_file"]}**: {batch[f"{item_name_single}_count"]} {item_name} - {batch["error"]}' for batch in summary_data["error_details"])}

## Files in this Directory
- `retry_summary.json` - Detailed error information
- `RETRY_INSTRUCTIONS.md` - This file
- `retry_batch_XX_failed.json` - Individual batch files ready for re-import

All retry files are formatted correctly for immediate import!
"""

        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions_content)

        self.logger.info(f"[RETRY] Created {len(retry_files)} retry files in {retry_dir}")
        self.logger.info(f"[RETRY] Summary saved to: {summary_file}")
        self.logger.info(f"[RETRY] Instructions saved to: {instructions_file}")
        self.logger.info(f"[RETRY] Ready for immediate re-import!")

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