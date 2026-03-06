# User Profile & Account Info - Implementation Plan

## 📊 Current State Analysis

### ✅ What Exists:
- **Profile Page**: `frontend/src/app/dashboard/settings/profile/page.tsx` (read-only display)
- **Settings Page**: Business/tenant settings with edit capabilities
- **Auth Hook**: `useAuth()` provides `userProfile` with user data
- **Backend**: `/auth/me` endpoint returns user profile
- **Tenant API**: `/tenants/me` for tenant CRUD operations

### ❌ What's Missing:
- User info display in sidebar
- User profile edit capabilities (name, email preferences)
- Backend user update endpoint
- Profile avatar/image support
- Account preferences section
- Activity/session management

---

## 🎨 UI Design & Structure (Following Current Theme)

### Color Palette (from globals.css):
```
Primary: #0b3c49 (dark teal)
Secondary: #167c8a (teal)
Accent: #6ad4b3 (mint)
CTA: #ffb347 (orange)
Ink: #1b2a2f (dark text)
Muted: #5c6b73 (gray text)
Success: #2ead7b (green)
```

### 1. Sidebar Enhancement

**Location**: Bottom of sidebar (above Sign Out button)

**Design**:
```
┌─────────────────────────────┐
│ [Avatar] John Doe          │  ← When expanded
│          john@example.com  │
│          Badge: Owner      │
└─────────────────────────────┘

When Collapsed:
┌───┐
│[A]│  ← Avatar with tooltip
└───┘
```

**Features**:
- User avatar (initials fallback)
- Name and email (when expanded)
- Role badge (Owner/Admin/User)
- Click to navigate to profile page
- Hover shows tooltip when collapsed

---

### 2. Enhanced Profile Page

**Route**: `/dashboard/settings/profile`

**Layout Sections**:

#### A. Header
- Page title: "Profile & Settings"
- Breadcrumb: Dashboard > Settings > Profile

#### B. Personal Information Card
```
┌─────────────────────────────────────┐
│ 👤 Personal Information             │
│ ─────────────────────────────────  │
│                                     │
│ Profile Picture                     │
│   [Avatar Circle] [Upload Button]  │
│                                     │
│ Full Name                           │
│   [Input: John Doe]                 │
│                                     │
│ Email Address                       │
│   john@example.com (Verified ✓)    │
│                                     │
│ Role                                │
│   Owner [Badge]                     │
│                                     │
│ Joined Date                         │
│   March 1, 2026                     │
│                                     │
│ [Save Changes Button]               │
└─────────────────────────────────────┘
```

#### C. Account Security Card
```
┌─────────────────────────────────────┐
│ 🔒 Account Security                 │
│ ─────────────────────────────────  │
│                                     │
│ Authentication                      │
│   AWS Cognito [Verified Badge]     │
│                                     │
│ Password                            │
│   Last changed: 7 days ago          │
│   [Change Password Button]          │
│                                     │
│ Two-Factor Authentication           │
│   Status: Disabled                  │
│   [Enable 2FA Button]               │
└─────────────────────────────────────┘
```

#### D. Company Workspace Card
```
┌─────────────────────────────────────┐
│ 🏢 Company Workspace                │
│ ─────────────────────────────────  │
│                                     │
│ Organization                        │
│   Acme Solutions Pvt Ltd            │
│                                     │
│ Tenant ID                           │
│   abc-123-def (Copy Icon)           │
│                                     │
│ Plan                                │
│   Pro Plan [Active Badge]           │
│                                     │
│ [Manage Company Settings →]         │
└─────────────────────────────────────┘
```

#### E. Preferences Card
```
┌─────────────────────────────────────┐
│ ⚙️ Preferences                      │
│ ─────────────────────────────────  │
│                                     │
│ Notifications                       │
│   [✓] Email notifications           │
│   [✓] System updates                │
│   [ ] Marketing emails              │
│                                     │
│ Display                             │
│   Theme: Light ○ Dark ○ System     │
│   Timezone: Asia/Kolkata            │
│                                     │
│ [Save Preferences Button]           │
└─────────────────────────────────────┘
```

#### F. Danger Zone Card
```
┌─────────────────────────────────────┐
│ ⚠️ Danger Zone                      │
│ ─────────────────────────────────  │
│                                     │
│ Delete Account                      │
│   Permanently delete your account   │
│   and all associated data           │
│   [Delete Account Button] (Red)     │
└─────────────────────────────────────┘
```

---

## 🔧 Backend Implementation

### New Endpoints Needed:

#### 1. User Profile Management
```python
# backend/app/api/v1/users.py (NEW FILE)

GET    /api/v1/users/me           # Get current user profile (already exists in auth)
PUT    /api/v1/users/me           # Update user profile
POST   /api/v1/users/me/avatar    # Upload avatar
DELETE /api/v1/users/me/avatar    # Remove avatar
GET    /api/v1/users/me/sessions  # Get active sessions
DELETE /api/v1/users/me/sessions  # Revoke all sessions
```

#### 2. User Preferences
```python
GET    /api/v1/users/me/preferences      # Get user preferences
PUT    /api/v1/users/me/preferences      # Update preferences
```

### Schema Additions:

#### User Update Schema
```python
# backend/app/schemas/user.py

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    # Email changes require verification, handled separately

class UserPreferences(BaseModel):
    email_notifications: bool = True
    system_updates: bool = True
    marketing_emails: bool = False
    theme: Literal["light", "dark", "system"] = "system"
    timezone: str = "Asia/Kolkata"

class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar_url: Optional[str]
    tenant_id: str
    tenant: Optional[dict]
    created_at: datetime
    preferences: Optional[UserPreferences]
```

### Database Migration:

```python
# Add to User model (backend/app/models/user.py)

avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
last_password_change: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

---

## 📝 Implementation Steps

### Phase 1: Backend Foundation (Priority: HIGH)
1. ✅ Create `backend/app/api/v1/users.py`
2. ✅ Add user update schemas
3. ✅ Implement PUT `/users/me` endpoint
4. ✅ Add database migration for new fields
5. ✅ Add user preferences endpoints

### Phase 2: Sidebar Enhancement (Priority: HIGH)
1. ✅ Add user avatar component
2. ✅ Display user info in sidebar footer
3. ✅ Add click handler to navigate to profile
4. ✅ Implement collapsed state with tooltip
5. ✅ Add role badge styling

### Phase 3: Profile Page Enhancement (Priority: MEDIUM)
1. ✅ Convert read-only fields to editable forms
2. ✅ Add avatar upload component
3. ✅ Implement save functionality
4. ✅ Add loading and success states
5. ✅ Add validation and error handling

### Phase 4: Advanced Features (Priority: LOW)
1. ⏳ Add preferences section
2. ⏳ Implement session management
3. ⏳ Add account deletion flow
4. ⏳ Add change password integration (via Cognito)
5. ⏳ Add activity log viewer

---

## 🎯 Quick Wins (Implement First)

### 1. Sidebar User Info (30 mins)
- Show avatar with initials
- Display name and email when expanded
- Add click to navigate to profile
- Role badge

### 2. Basic Profile Edit (1 hour)
- Make name field editable
- Add save button
- Connect to backend update endpoint
- Show success/error feedback

### 3. Backend User Update (1 hour)
- Create users.py router
- Add PUT /users/me endpoint
- Update user model if needed
- Add audit logging

---

## 🎨 Component Structure

### Frontend Components to Create/Modify:

```
frontend/src/
├── components/
│   ├── layout/
│   │   └── sidebar.tsx                    [MODIFY] Add user info section
│   ├── profile/
│   │   ├── avatar-upload.tsx              [CREATE] Avatar upload component
│   │   ├── profile-info-card.tsx          [CREATE] Personal info card
│   │   ├── security-card.tsx              [CREATE] Security settings
│   │   ├── preferences-card.tsx           [CREATE] User preferences
│   │   └── user-avatar.tsx                [CREATE] Reusable avatar component
└── app/
    └── dashboard/
        └── settings/
            └── profile/
                └── page.tsx                [MODIFY] Enhanced profile page
```

### Backend Files to Create/Modify:

```
backend/app/
├── api/v1/
│   ├── users.py                           [CREATE] User management endpoints
│   └── router.py                          [MODIFY] Include users router
├── schemas/
│   └── user.py                            [MODIFY] Add update/response schemas
├── models/
│   └── user.py                            [MODIFY] Add avatar_url, preferences
└── services/
    └── user_service.py                    [CREATE] User business logic
```

---

## 🚀 Next Steps

**Choose your approach:**

### Option A: Quick Implementation (3-4 hours)
Focus on Quick Wins only:
1. Sidebar user info
2. Basic profile edit
3. Backend update endpoint

### Option B: Full Implementation (2 days)
Complete all phases except advanced features

### Option C: MVP + Polish (3-4 days)
Everything including advanced features

---

## 📋 Testing Checklist

- [ ] User can see their info in sidebar
- [ ] Clicking sidebar user navigates to profile
- [ ] User can edit their name
- [ ] Changes persist after refresh
- [ ] Avatar displays correctly
- [ ] Role badge shows correct role
- [ ] Responsive on mobile devices
- [ ] Loading states work correctly
- [ ] Error messages are clear
- [ ] Audit log records changes

---

**Ready to implement? Let me know which approach you'd like to take!**
