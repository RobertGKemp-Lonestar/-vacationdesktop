# VacationDesktop

A comprehensive multi-tenant web application for Travel Advisors to manage their business operations with a robust Role-Based Access Control (RBAC) system.

## 🚀 Project Overview

VacationDesktop is designed as a multi-tenant platform that allows travel advisor agencies to manage:

- **Customer Relationship Management (CRM)**
- **Supplier/Vendor Management** 
- **Trip Building & Distribution**
- **Invoice & Payment Processing**
- **Email Marketing Campaigns**
- **Forms Hub**
- **Destination, Tour & Cruise Hubs**
- **Network Portal for advisor collaboration**
- **Admin/Support/Sales tools**

## 🏗️ Architecture

### Multi-Tenant RBAC System

The application implements a sophisticated 5-tier role hierarchy:

#### System Roles (Platform Management)
1. **Super Admin** - Full system access across all tenants
2. **System Admin** - System administration and tenant management  
3. **Help Desk User** - Customer support functions

#### Client Roles (Tenant-Specific)
4. **Client Admin** - Full access within tenant organization
5. **Client User** - Standard access with optional financial permissions

### Technical Stack

- **Backend:** Django 4.2.23 with Python 3.9
- **Database:** SQLite (development) / PostgreSQL (production)
- **Authentication:** Custom User model with MFA support via django-otp
- **Frontend:** Bootstrap 5 with custom CSS and Font Awesome icons
- **Security:** Comprehensive audit logging and permission-based access control

## 🔐 Security Features

- **Multi-Factor Authentication (MFA)** support
- **Granular permissions** across 15+ functional categories
- **Audit logging** for all user actions
- **IP tracking** and session management
- **Role-based UI rendering** based on user permissions
- **Tenant isolation** ensuring data privacy

## 📊 Database Schema

### Core Models

- **User** - Extended Django user with tenant association and RBAC fields
- **Tenant** - Multi-tenant organizations (travel advisor agencies)
- **Role** - Hierarchical role definitions
- **Permission** - Granular permission system with categories
- **RolePermission** - Role-to-permission mappings
- **UserPermissionOverride** - Individual user permission exceptions
- **AuditLog** - Comprehensive activity tracking

## 🎨 User Interface

### Dashboard Features
- **Role-specific dashboards** with relevant statistics
- **Quick action panels** based on user permissions
- **Recent activity tracking**
- **MFA status indicators**
- **Responsive design** for desktop and mobile

### Visual Design
- **Bootstrap 5** framework with custom CSS variables
- **Gradient cards** and modern UI components
- **Role-based color coding** for user identification
- **Professional travel industry aesthetic**

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Virtual environment (recommended)
- PostgreSQL (for production)

### Installation

1. **Clone and setup virtual environment:**
   ```bash
   cd VacationDesktop
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install django psycopg2-binary django-otp qrcode pillow python-decouple
   ```

3. **Configure environment:**
   ```bash
   # .env file is already configured for development
   # Update database settings for production use
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Set up RBAC system:**
   ```bash
   python manage.py setup_rbac
   ```

6. **Create superuser:**
   ```bash
   python manage.py create_superuser
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver
   ```

### Default Login Credentials
- **Username:** admin
- **Password:** admin123
- **Role:** Super Admin

## 🌐 Accessing the Application

- **Main Application:** http://localhost:8000/
- **Django Admin:** http://localhost:8000/admin/
- **Login Page:** http://localhost:8000/login/
- **Dashboard:** http://localhost:8000/dashboard/
- **Password Reset:** http://localhost:8000/password-reset/
- **Profile Management:** http://localhost:8000/profile/

## 📋 Available Features

### Current Implementation
✅ Complete RBAC system with 5 roles  
✅ Multi-tenant architecture  
✅ User authentication with audit logging  
✅ Password reset functionality with email notifications  
✅ Profile management (edit profile, change password)  
✅ Responsive dashboard with role-specific views  
✅ Django admin integration  
✅ MFA framework setup  
✅ Professional UI with Bootstrap 5  

### Planned Features
🔄 **Implement user authentication with MFA support** (framework ready)  
📋 CRM module for customer management  
📋 Supplier/vendor management system  
📋 Trip builder and itinerary tools  
📋 Invoice and payment processing  
📋 Email marketing campaign tools  
📋 Forms hub for custom forms  
📋 Destination/tour/cruise content management  
📋 Network portal for advisor collaboration  

## 🔧 Development Commands

### RBAC Management
```bash
# Setup initial roles and permissions
python manage.py setup_rbac

# Create superuser with proper role assignment
python manage.py create_superuser --username admin --email admin@example.com
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations  
python manage.py migrate

# Reset database (development only)
rm db.sqlite3
python manage.py migrate
python manage.py setup_rbac
```

## 🏢 Multi-Tenant Usage

### System Users (Platform Management)
- Access tenant management and system administration
- View cross-tenant analytics and reports
- Manage user roles and permissions across all tenants

### Client Users (Travel Advisors)
- Isolated to their specific tenant/agency
- Access CRM, trip building, and financial tools
- Collaborate within their organization boundaries

## 🔍 Permission Categories

The system includes granular permissions across these categories:

- **User Management** - User account administration
- **Tenant Management** - Organization management (system users only)
- **CRM** - Customer relationship management
- **Supplier Management** - Vendor/partner relationships
- **Forms Hub** - Custom form creation and management
- **Email Marketing** - Campaign creation and distribution
- **Trip Builder** - Itinerary creation and management
- **Invoice System** - Billing and invoicing
- **Payment System** - Payment processing
- **Financial Data** - Sensitive financial information (special access)
- **Destination/Tour/Cruise Hubs** - Content management
- **Network Portal** - Inter-advisor collaboration
- **Reports & Analytics** - Business intelligence

## 🛡️ Security Best Practices

- All user actions are logged in the audit trail
- Sensitive operations require appropriate role permissions
- Financial data access is specially controlled for Client Users
- MFA can be enabled for enhanced security
- Session management and IP tracking
- CSRF protection and secure headers

## 📁 Project Structure

```
VacationDesktop/
├── rbac/                     # RBAC Django app
│   ├── models.py            # User, Role, Permission, Tenant models
│   ├── admin.py             # Django admin configuration
│   ├── views.py             # Authentication and dashboard views
│   ├── management/commands/ # Setup commands
│   └── migrations/          # Database migrations
├── templates/               # HTML templates
│   ├── base.html           # Base template with navigation
│   └── rbac/               # RBAC-specific templates
├── static/css/             # Custom CSS styling
├── vacationdesktop/        # Django project settings
└── manage.py               # Django management script
```

## 🤝 Contributing

This project is designed as a foundation for a comprehensive travel advisor platform. The RBAC system and multi-tenant architecture provide a solid base for building out the complete feature set defined in VacationDesktop.txt.

## 📄 License

This project is in development as a proof-of-concept for a multi-tenant travel advisor business platform.

---

**Status:** ✅ RBAC Foundation Complete - Ready for feature module development