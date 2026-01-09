
# 藥品進存貨系統 (Pharmacy Inventory System) API 規格書

**版本**: 1.0

**基底 URL**: `/api`

**格式**: JSON

## 📋 簡介

本文件描述藥品管理系統的後端 API 介面，提供藥品資料的 **CRUD** (新增、讀取、更新、刪除) 功能。

### 通用請求標頭 (Request Headers)

若使用 **Ngrok** 進行連線，為避免瀏覽器警告頁面攔截 API 請求，前端需在所有請求中加入以下 Header：

```http
Content-Type: application/json
ngrok-skip-browser-warning: true

```

### 通用回應格式

API 回應皆為 JSON 格式，包含 `status` 欄位以指示操作結果。

**成功回應範例:**

```json
{
  "status": "success",
  "data": { ... }  // 或 "message": "..."
}

```

**錯誤回應範例:**

```json
{
  "status": "error",
  "message": "錯誤描述訊息"
}

```

---

## 💊 資料模型 (Medicine Object)

| 欄位名稱 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| `id` | Integer | - | 藥品唯一識別碼 (系統自動產生) |
| `name` | String | ✅ | 藥品名稱 |
| `category` | String | - | 藥品類別 (如：抗生素、維他命) |
| `price` | Float | - | 價格 |
| `stock` | Integer | - | 庫存數量 |
| `expiry_date` | String | - | 有效期限 (格式：YYYY-MM-DD) |

---

## 🚀 API 端點詳情

### 1. 取得所有藥品列表

取得資料庫中所有的藥品資料，按 ID 降序排列。

* **URL**: `/medicines`
* **Method**: `GET`
* **成功回應 (200 OK)**:

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "普拿疼",
      "category": "止痛藥",
      "price": 150.0,
      "stock": 50,
      "expiry_date": "2025-12-31"
    },
    {
      "id": 2,
      "name": "維他命C",
      "category": "保健品",
      "price": 300.0,
      "stock": 20,
      "expiry_date": "2026-05-20"
    }
  ]
}

```

---

### 2. 取得單一藥品

根據 ID 取得特定藥品的詳細資料。

* **URL**: `/medicines/{id}`
* **Method**: `GET`
* **URL 參數**: `id` (藥品 ID)
* **成功回應 (200 OK)**:

```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "普拿疼",
    "category": "止痛藥",
    "price": 150.0,
    "stock": 50,
    "expiry_date": "2025-12-31"
  }
}

```

* **失敗回應 (404 Not Found)**:

```json
{
  "status": "error",
  "message": "找不到該藥品"
}

```

---

### 3. 新增藥品

建立一筆新的藥品資料。

* **URL**: `/medicines`
* **Method**: `POST`
* **Request Body (JSON)**:

```json
{
  "name": "阿斯匹靈",
  "category": "心血管",
  "price": 120,
  "stock": 100,
  "expiry_date": "2024-10-10"
}

```

*(注意：`name` 為必填欄位)*

* **成功回應 (201 Created)**:

```json
{
  "status": "success",
  "message": "藥品新增成功",
  "id": 3
}

```

---

### 4. 更新藥品

更新現有的藥品資料。

* **URL**: `/medicines/{id}`
* **Method**: `PUT`
* **URL 參數**: `id` (藥品 ID)
* **Request Body (JSON)**:

```json
{
  "name": "阿斯匹靈 (加強版)",
  "category": "心血管",
  "price": 150,
  "stock": 90,
  "expiry_date": "2024-12-31"
}

```

* **成功回應 (200 OK)**:

```json
{
  "status": "success",
  "message": "藥品更新成功"
}

```

* **失敗回應 (404 Not Found)**: 若 ID 不存在。

---

### 5. 刪除藥品

移除指定的藥品資料。

* **URL**: `/medicines/{id}`
* **Method**: `DELETE`
* **URL 參數**: `id` (藥品 ID)
* **成功回應 (200 OK)**:

```json
{
  "status": "success",
  "message": "藥品已刪除"
}

```

* **失敗回應 (404 Not Found)**: 若該 ID 已經被刪除或不存在。
