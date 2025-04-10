
# Payment API Documentation

## Overview
This API provides endpoints for managing money transfers, payments, and related operations. It supports both single and bulk transfers, status checking, and administrative functions.

## Base URL
`{{payment_api}}` (Configure in your environment variables)

---

## Authentication
All endpoints require Bearer token authentication:
```http
Authorization: Bearer {{API_TOKEN}} or {{ADMIN_TOKEN}}
```

---

## Transfer Endpoints

### 1. Get Pending Approvals
**GET** `/transfers/approvals-pending`

Returns batch transfers waiting for approval.

**Response:**
```json
[
  {
    "created_at": "2025-04-09 16:38:05",
    "number_transaction": 3,
    "status_code": "BP104",
    "total_amount": "2400.0000000000",
    "tracking_id": "1c986d8e-7e1b-4bc0-bee8-5e7c6561aef0"
  }
]
```

---

### 2. Initiate Single Transfer
**POST** `/transfers/initiate/single`

Initiate a transfer to a single recipient.

**Request Body:**
```python
{
  "records": {
    "name": "kimani",
    "phone": 254793536684,
    "amount": 5000
  },
  "requires_approval": "YES"
}
```

**Response:**
```json
{
  "data": "",
  "message": "",
  "tracking_id": "32f54fde-5175-486b-96b9-ba6edddde70e"
}
```

---

### 3. Initiate Bulk Transfers
**POST** `/transfers/initiate/bulk`

Initiate transfers to multiple recipients.

**Request Body:**
```json
{
  "records": [
    {
      "name": "ajay",
      "phone": "254714872412",
      "amount": 700
    },
    {
      "name": "gatu",
      "phone": "254714872442",
      "amount": 800
    }
  ],
  "requires_approval": "YES"
}
```

**Response:**
```json
{
  "message": "",
  "tracking_id": ""
}
```

---

### 4. Check Transfer Status
**POST** `/transfers/check-status`

Check the status of a specific transfer.

**Request Body:**
```json
{
  "tracking_id": "00b6e6d3-f28c-4079-8e8b-f1272bbef0cd"
}
```

**Response:**
```json
{
  "data": [
    {
      "created_at": "2025-04-10T12:34:56",
      "number_transaction": 1,
      "status_code": "COMPLETED",
      "total_amount": "500.00",
      "tracking_id": "00b6e6d3-f28c-4079-8e8b-f1272bbef0cd"
    }
  ],
  "message": "success"
}
```

---

### 5. Approve Batch Transfer
**POST** `/transfers/approve`

Approve a pending batch transfer.

**Request Body:**
```json
{
  "batch_id": "32f54fde-5175-486b-96b9-ba6edddde70e"
}
```

---

### 6. Inspect Transfers
**POST** `/transfers/inspect`

Retrieve transfers based on date and logic.

**Request Body:**
```json
{
  "date": "2025-04-10",
  "logic": "le"
}
```

**Response:**
```json
{
  "data": [
    {
      "created_at": "2025-04-10T09:15:22",
      "number_transaction": 2,
      "status_code": "PENDING",
      "total_amount": "1500.00",
      "tracking_id": "3bb8a3fe-d65d-4a5e-afbd-6c6de3775ac9",
      "transfers": [
        {
          "account": "123456",
          "amount": "750.00",
          "charges": "10.00",
          "created_at": "2025-04-10T09:15:22",
          "name": "John Doe",
          "reference_id": "ref123",
          "status_code": "PENDING"
        }
      ]
    }
  ],
  "message": "success"
}
```

---

## Payment Endpoints

### 1. Initiate Payment
**POST** `/pay`

Initiate a payment collection request.

**Request Body:**
```json
{
  "phone": "2544793536684",
  "amount": 700,
  "orderid": "thisismytestorder"
}
```

---

### 2. Check Payment Status
**GET** `/check-status`

Check the status of a payment request.

**Query Parameters:**
- `invoice_id`: Payment reference ID

---

## Status Codes

| Code    | Description       |
|---------|-------------------|
| BP100   | Pending Approval  |
| BP103   | Processing        |
| BP104   | Awaiting Approval |


---

## Error Handling

Common error responses:

```json
{
  "error": "Description of error",
  "message": "Human-readable message"
}
```

Status codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

---

## Examples

### Initiate Single Transfer
```bash
curl -X POST \
  {{payment_api}}/transfers/initiate/single \
  -H 'Authorization: Bearer {{API_TOKEN}}' \
  -H 'Content-Type: application/json' \
  -d '{
    "records": {
      "name": "kimani",
      "phone": 254793536684,
      "amount": 5000
    },
    "requires_approval": "YES"
  }'
```

### Check Transfer Status
```bash
curl -X POST \
  {{payment_api}}/transfers/check-status \
  -H 'Authorization: Bearer {{ADMIN_TOKEN}}' \
  -H 'Content-Type: application/json' \
  -d '{
    "tracking_id": "00b6e6d3-f28c-4079-8e8b-f1272bbef0cd"
  }'
```

---

## Notes
1. All amounts should be in numeric format (e.g., 5000 for 5000.00)
2. Phone numbers should be in international format without '+' (e.g., 254712345678)
3. Timestamps are in ISO 8601 format
```
