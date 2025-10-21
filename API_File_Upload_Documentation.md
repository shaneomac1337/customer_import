# File Upload API Documentation

This document describes how to upload files (images) to the GK Software media API using curl commands.

## Table of Contents
- [Authentication](#authentication)
- [File Upload](#file-upload)
- [Postman Testing](#postman-testing)
- [Python Implementation](#python-implementation)
- [Troubleshooting](#troubleshooting)

## Authentication

### Get Bearer Token

Before uploading files, you need to obtain a Bearer token for authentication.

#### Method 1: Using Basic Auth (Recommended)
```bash
curl --location 'https://test.ahd.cloud4retail.co/auth-service/tenants/001/oauth/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--user 'launchpad:1zQbeyL5NdDj5BGTaqo3' \
--data-urlencode 'username=1' \
--data-urlencode 'password=1' \
--data-urlencode 'grant_type=password'
```

#### Method 2: Using Encoded Basic Auth
```bash
curl --location 'https://test.ahd.cloud4retail.co/auth-service/tenants/001/oauth/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--header 'Authorization: Basic bGF1bmNocGFkOjF6UWJleUw1TmREajVCR1RhcW8z' \
--data-urlencode 'username=1' \
--data-urlencode 'password=1' \
--data-urlencode 'grant_type=password'
```

**Note:** The Basic Auth credentials are:
- Username: `launchpad`
- Password: `1zQbeyL5NdDj5BGTaqo3`
- Encoded: `bGF1bmNocGFkOjF6UWJleUw1TmREajVCR1RhcW8z`

### Response Format
The authentication response will contain:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "GK"
}
```

Copy the `access_token` value for use in file upload requests.

## File Upload

### Upload Image File

```bash
curl --location 'https://test.ahd.cloud4retail.co/dsg/services/rest/media/v1/files/image/item/test_img.PNG' \
--header 'accept: */*' \
--header 'authorization: Bearer YOUR_ACCESS_TOKEN_HERE' \
--header 'gk-accept-redirect: 308' \
--form 'content=@"/path/to/your/image.png";type=image/png'
```

### Parameters Explanation

| Parameter | Description |
|-----------|-------------|
| `URL` | The endpoint URL with the target filename |
| `accept: */*` | Accept any response content type |
| `authorization: Bearer` | Your access token from authentication |
| `gk-accept-redirect: 308` | Custom header for GK API redirect handling |
| `content=@"filepath"` | The file to upload (@ prefix for file path) |
| `type=image/png` | Explicitly set the MIME type |

### Supported File Types

Based on the API structure, supported image types likely include:
- `image/png`
- `image/jpeg`
- `image/jpg`
- `image/gif`
- `image/webp`

### Example with Different File Types

**PNG File:**
```bash
--form 'content=@"/path/to/image.png";type=image/png'
```

**JPEG File:**
```bash
--form 'content=@"/path/to/image.jpg";type=image/jpeg'
```

**GIF File:**
```bash
--form 'content=@"/path/to/image.gif";type=image/gif'
```

## Postman Testing

### Setup Steps

1. **Create New Request**
   - Method: `POST`
   - URL: `https://test.ahd.cloud4retail.co/dsg/services/rest/media/v1/files/image/item/your_filename.png`

2. **Headers Tab**
   ```
   Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
   accept: */*
   gk-accept-redirect: 308
   ```
   
   **Important:** Do NOT add `Content-Type` header manually - Postman handles this automatically for form-data.

3. **Body Tab**
   - Select **form-data**
   - Add key: `content`
   - Change type from "Text" to **"File"**
   - Select your image file

4. **Send Request**

### Expected Responses

**Success (200/201):**
```json
{
  "status": "success",
  "message": "File uploaded successfully"
}
```

**Error (415 - Unsupported Media Type):**
```json
{
  "message": "Resource (, application/octet-stream) was rejected by input/accept filter",
  "timestamp": "2025-07-24T17:47:26.641+0000",
  "status": 415,
  "url": "https://test.ahd.cloud4retail.co/dsg/services/rest/media/v1/files/image/item/test_img.PNG"
}
```

## Python Implementation

### Using requests library

```python
import requests

# Step 1: Get access token
auth_url = "https://test.ahd.cloud4retail.co/auth-service/tenants/001/oauth/token"
auth_data = {
    'username': '1',
    'password': '1',
    'grant_type': 'password'
}
auth_headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

# Using basic auth
auth_response = requests.post(
    auth_url, 
    data=auth_data, 
    headers=auth_headers,
    auth=('launchpad', '1zQbeyL5NdDj5BGTaqo3')
)

access_token = auth_response.json()['access_token']

# Step 2: Upload file
upload_url = "https://test.ahd.cloud4retail.co/dsg/services/rest/media/v1/files/image/item/test_img.PNG"
upload_headers = {
    'authorization': f'Bearer {access_token}',
    'accept': '*/*',
    'gk-accept-redirect': '308'
}

with open('test_img.PNG', 'rb') as file:
    files = {
        'content': ('test_img.PNG', file, 'image/png')
    }
    upload_response = requests.post(upload_url, headers=upload_headers, files=files)

print(f"Upload status: {upload_response.status_code}")
print(f"Response: {upload_response.text}")
```

## Troubleshooting

### Common Issues

1. **415 Unsupported Media Type**
   - **Cause:** File sent as `application/octet-stream` instead of proper image MIME type
   - **Solution:** Explicitly specify the content type: `;type=image/png`

2. **401 Unauthorized**
   - **Cause:** Invalid or expired Bearer token
   - **Solution:** Get a new access token using the authentication endpoint

3. **403 Forbidden**
   - **Cause:** Token valid but insufficient permissions
   - **Solution:** Check user permissions for media upload

4. **404 Not Found**
   - **Cause:** Incorrect API endpoint URL
   - **Solution:** Verify the URL structure and filename

### Debug Tips

1. **Check token expiration:** JWT tokens typically expire after 1 hour
2. **Verify file path:** Ensure the file exists and path is correct
3. **Test with Postman first:** Easier to debug than command line
4. **Check file size limits:** Large files may be rejected
5. **Verify MIME type:** Use `file --mime-type filename` to check actual file type

### Token Expiration

Bearer tokens expire after a certain time (usually 1 hour). If you get 401 errors, obtain a new token:

```bash
# Quick token refresh
TOKEN=$(curl -s --location 'https://test.ahd.cloud4retail.co/auth-service/tenants/001/oauth/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--user 'launchpad:1zQbeyL5NdDj5BGTaqo3' \
--data-urlencode 'username=1' \
--data-urlencode 'password=1' \
--data-urlencode 'grant_type=password' | jq -r '.access_token')

echo "New token: $TOKEN"
```

---

**Last Updated:** July 24, 2025  
**API Version:** v1  
**Environment:** Test (test.ahd.cloud4retail.co)
