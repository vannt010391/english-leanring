# Admin Features Quick Reference Guide
## VocabMaster - User Management & System Vocabulary

---

## 🚀 Quick Start

### Access Admin Pages
1. **User Management**: `/admin-users/`
2. **System Vocabulary Management**: `/admin-system-vocabulary/`

*Note: Only admin users can access these pages. Regular users are redirected to dashboard.*

---

## 👥 User Management API

### List All Users
```bash
GET /api/auth/users/
Authorization: Token {token}
Query Params: ?page=1&page_size=20
```

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "john",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "admin",
      "is_active": true,
      "date_joined": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### Get Single User
```bash
GET /api/auth/users/1/
Authorization: Token {token}
```

### Create New User
```bash
POST /api/auth/users/
Authorization: Token {token}
Content-Type: application/json

{
  "username": "jane_doe",
  "email": "jane@example.com",
  "password": "SecurePassword123",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "learner"
}
```

### Update User
```bash
PUT /api/auth/users/1/
Authorization: Token {token}
Content-Type: application/json

{
  "username": "john_updated",
  "email": "john_new@example.com",
  "first_name": "Jonathan",
  "last_name": "Smith",
  "role": "admin",
  "password": "NewPassword123"
}
```
*Password is optional. Leave empty to keep current password.*

### Delete User
```bash
DELETE /api/auth/users/1/
Authorization: Token {token}
```

### Assign Role to User
```bash
POST /api/auth/users/1/assign_role/
Authorization: Token {token}
Content-Type: application/json

{
  "role": "admin"
}
```
*Valid roles: "admin", "learner"*

### Activate User
```bash
POST /api/auth/users/1/activate/
Authorization: Token {token}
```

### Deactivate User
```bash
POST /api/auth/users/1/deactivate/
Authorization: Token {token}
```

### List Active Users Only
```bash
GET /api/auth/users/active_users/
Authorization: Token {token}
```

---

## 📚 System Vocabulary API

### List System Vocabulary
```bash
GET /api/vocabulary/system/
Authorization: Token {token}
Query Params: ?page=1&page_size=20&search=apple&level=A1&word_type=noun&topic=1
```

### Get Single Vocabulary Item
```bash
GET /api/vocabulary/system/1/
Authorization: Token {token}
```

### Create System Vocabulary
```bash
POST /api/vocabulary/system/
Authorization: Token {token}
Content-Type: application/json

{
  "word": "apple",
  "meaning": "A round fruit",
  "meaning_vi": "Một loại quả",
  "phonetics": "/ˈæpl/",
  "word_type": "noun",
  "level": "A1",
  "example_sentence": "I like apples.",
  "note": "Common beginner word",
  "topic_ids": [1, 2]
}
```

**Valid Fields:**
- `word` (required): The English word
- `meaning` (required): English definition
- `meaning_vi` (optional): Vietnamese translation
- `phonetics` (optional): Phonetic transcription
- `word_type` (optional): noun, verb, adjective, adverb, preposition, conjunction, pronoun, phrase, idiom
- `level` (optional): A1, A2, B1, B2, C1, C2
- `example_sentence` (optional): Example usage
- `note` (optional): Additional notes
- `topic_ids` (optional): Array of topic IDs

### Update System Vocabulary
```bash
PUT /api/vocabulary/system/1/
Authorization: Token {token}
Content-Type: application/json

{
  "word": "apple",
  "meaning": "A round fruit that grows on trees",
  "meaning_vi": "Một loại quả hình tròn",
  "phonetics": "/ˈæpəl/",
  "word_type": "noun",
  "level": "A1",
  "example_sentence": "Apple is my favorite fruit.",
  "note": "Very common",
  "topic_ids": [1]
}
```

### Delete System Vocabulary
```bash
DELETE /api/vocabulary/system/1/
Authorization: Token {token}
```

### Bulk Import CSV
```bash
POST /api/vocabulary/system/import_csv/
Authorization: Token {token}
Content-Type: multipart/form-data

Form Data:
- file: [CSV file]
- topic_ids: [1, 2, 3] (optional)
```

**CSV Format** (Header required):
```csv
word,meaning,meaning_vi,phonetics,word_type,level,note,example_sentence
apple,A round fruit,Một loại quả,/ˈæpl/,noun,A1,Common word,I eat an apple.
beautiful,Pleasing to look at,Đẹp,/ˈbjuːtɪfl/,adjective,A2,Common adjective,She is beautiful.
```

**CSV Import Response:**
```json
{
  "message": "Successfully imported 50 new system vocabulary items. Updated topics for 10 existing items.",
  "created_count": 50,
  "updated_count": 10,
  "errors": [
    "Row 5: Missing required fields (word and meaning)",
    "Row 12: Invalid level: X5"
  ]
}
```

---

## 🎓 Learner Vocabulary API

### Get All Vocabulary (System + Personal)
```bash
GET /api/vocabulary/
Authorization: Token {token}
Query Params: ?page=1&page_size=20&search=apple&level=A1&status=new
```

### Get Personal Vocabulary Only
```bash
GET /api/vocabulary/personal/
Authorization: Token {token}
```

### Get System Vocabulary (Read-only for Learners)
```bash
GET /api/vocabulary/system/
Authorization: Token {token}
```

### Create Personal Vocabulary
```bash
POST /api/vocabulary/
Authorization: Token {token}
Content-Type: application/json

{
  "word": "custom_word",
  "meaning": "My custom meaning",
  "meaning_vi": "Nghĩa của tôi",
  "word_type": "noun",
  "level": "B1",
  "topic_ids": [1]
}
```
*Note: System vocabulary cannot be created by learners. Automatically marked as personal.*

### Update Personal Vocabulary
```bash
PUT /api/vocabulary/1/
Authorization: Token {token}
Content-Type: application/json

{
  "word": "updated_word",
  "meaning": "Updated meaning"
}
```
*Only own vocabulary can be updated. System vocabulary is read-only.*

### Delete Personal Vocabulary
```bash
DELETE /api/vocabulary/1/
Authorization: Token {token}
```

---

## 🔍 Filtering & Query Parameters

### Search
```bash
GET /api/vocabulary/system/?search=apple
```

### Filter by Level
```bash
GET /api/vocabulary/system/?level=A1
# Valid: A1, A2, B1, B2, C1, C2
```

### Filter by Word Type
```bash
GET /api/vocabulary/system/?word_type=noun
# Valid: noun, verb, adjective, adverb, preposition, conjunction, pronoun, phrase, idiom
```

### Filter by Topic
```bash
GET /api/vocabulary/system/?topic=1
```

### Pagination
```bash
GET /api/vocabulary/system/?page=2&page_size=50
```

---

## 🧑‍💼 Admin UI Features

### User Management Page (`/admin-users/`)

**Features:**
- 👥 View all users in table format
- 🔍 Search by username or email
- ➕ Create new users with modal form
- ✏️ Edit user details
- 🔄 Change user roles
- ✅ Activate/Deactivate users
- 🗑️ Delete users (with confirmation)
- 📄 Paginated results (20 per page)

**User Columns:**
- Username
- Email
- Full Name
- Role (badge: Admin/Learner)
- Status (badge: Active/Inactive)
- Join Date
- Actions

### System Vocabulary Page (`/admin-system-vocabulary/`)

**Features:**
- 📚 View all system vocabulary
- 📤 Drag & drop CSV import
- ➕ Add individual vocabulary items
- ✏️ Edit vocabulary details
- 🗑️ Delete vocabulary items
- 🔍 Search by word or meaning
- 🏷️ Filter by level (A1-C2)
- 📝 Filter by word type
- 📦 Topic assignment

**Vocabulary Columns:**
- Word
- English Meaning (truncated)
- Vietnamese Meaning (truncated)
- Word Type
- Level (color-coded badge)
- Topics
- Actions

**CSV Import:**
- Drag and drop file or click to upload
- Automatic error reporting
- Shows import summary (created/updated/errors)
- Optional topic assignment

---

## 🔐 Permissions Summary

| Operation | Admin | Learner |
|-----------|-------|---------|
| View users | ✅ | ❌ |
| Create user | ✅ | ❌ |
| Edit user | ✅ | ❌ |
| Delete user | ✅ | ❌ |
| Assign role | ✅ | ❌ |
| Create system vocab | ✅ | ❌ |
| Edit system vocab | ✅ | ❌ |
| Delete system vocab | ✅ | ❌ |
| Import vocab CSV | ✅ | ❌ |
| View system vocab | ✅ | ✅ |
| Create personal vocab | ✅ | ✅ |
| Edit own vocab | ✅ | ✅ |
| Delete own vocab | ✅ | ✅ |

---

## 🛠️ Common Tasks

### Create a New Admin User
```bash
POST /api/auth/users/
{
  "username": "admin_user",
  "email": "admin@example.com",
  "password": "AdminPass123",
  "role": "admin"
}
```
Then use the UI to set first/last name.

### Import 50 Vocabulary Items from CSV
1. Go to `/admin-system-vocabulary/`
2. Drag CSV file to upload area or click to select
3. Check import summary for success/errors
4. New vocabulary appears in table

### Change User from Learner to Admin
```bash
POST /api/auth/users/5/assign_role/
{
  "role": "admin"
}
```

### Filter System Vocabulary by Level
```bash
GET /api/vocabulary/system/?level=B1&page_size=100
```

### Deactivate a User
```bash
POST /api/auth/users/3/deactivate/
```

---

## 📊 Response Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET, PUT, POST (successful) |
| 201 | Created | POST (new resource created) |
| 204 | No Content | DELETE (successful) |
| 400 | Bad Request | Invalid data in request |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Unexpected error |

---

## 🔗 Useful Links

- Admin Users: `/admin-users/`
- System Vocabulary: `/admin-system-vocabulary/`
- Learner Vocabulary: `/vocabulary/`
- Dashboard: `/dashboard/`
- Django Admin: `/admin/`

---

## 💡 Tips & Tricks

1. **CSV Import**: Ensure headers match exactly:
   ```
   word,meaning,meaning_vi,phonetics,word_type,level,note,example_sentence
   ```

2. **Bulk Operations**: Import multiple vocabularies at once via CSV

3. **User Deactivation**: Deactivate instead of delete to preserve history

4. **Role Changes**: Change user role on-the-fly without re-login needed

5. **Search**: Use tab switching to filter between system and personal vocab

---

**Last Updated**: January 20, 2026
