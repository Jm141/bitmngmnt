# Inventory Management System

A comprehensive Django-based inventory management system with advanced user management, role-based permissions, and SQL injection protection.

## Features

### 🔐 Security Features
- **SQL Injection Protection**: All database queries use Django ORM to prevent SQL injection attacks
- **CSRF Protection**: Built-in CSRF protection for all forms
- **XSS Protection**: Input validation and sanitization
- **Secure Headers**: HSTS, X-Frame-Options, and other security headers
- **Audit Logging**: Complete audit trail for all user actions

### 👥 User Management
- **Role-Based Access Control**: Super Admin, Admin, and Staff roles
- **Permission System**: Granular permissions for different operations
- **User CRUD Operations**: Create, Read, Update, Delete users
- **User Relationships**: Manager-subordinate relationships
- **Account Management**: Activate/deactivate users

### 🛡️ Permission System
- **Super Admin**: Full system access, can manage all users and permissions
- **Admin**: Can manage staff users and assign permissions
- **Staff**: Basic access with assigned permissions
- **Permission Types**: Inventory, User, Reports, and Settings permissions

## Installation

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd capstone
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   - Create MySQL database named `inventory_mgnmnt`
   - Update database credentials in `capstone/settings.py` if needed
   - Default credentials:
     - Host: localhost
     - Port: 3306
     - Database: inventory_mgnmnt
     - Username: root
     - Password: 1234

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create super admin user**
   ```bash
   python manage.py create_superadmin --first-name Admin --last-name User --email admin@inventory.com --password admin123 --birthday 1990-01-01
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open browser and go to `http://127.0.0.1:8000`
   - Login with the super admin credentials

## Database Schema

### User Table
- `id`: UUID primary key
- `username`: Unique username
- `email`: Email address
- `first_name`, `last_name`: User names
- `role`: super_admin, admin, or staff
- `phone_number`: Contact number
- `address`: User address
- `birthday`: Date of birth (age calculated automatically)
- `is_active`: Account status
- `created_at`, `updated_at`: Timestamps
- `created_by`: Reference to user who created this user

### UserAccess Table
- `id`: UUID primary key
- `user`: Foreign key to User
- `permission_type`: Type of permission
- `granted_by`: User who granted the permission
- `granted_at`: When permission was granted
- `expires_at`: Optional expiration date
- `is_active`: Permission status

### UserLinks Table
- `id`: UUID primary key
- `user`: Foreign key to User
- `linked_user`: Foreign key to User
- `link_type`: manager, subordinate, or colleague
- `created_at`: When link was created
- `is_active`: Link status

### AuditLog Table
- `id`: UUID primary key
- `user`: User who performed the action
- `action_type`: Type of action performed
- `target_model`: Model that was affected
- `target_id`: ID of the affected record
- `description`: Description of the action
- `ip_address`: IP address of the user
- `user_agent`: Browser information
- `timestamp`: When action was performed

## Security Implementation

### SQL Injection Protection
- All database queries use Django ORM
- Custom UserManager with safe query methods
- Input validation and sanitization
- Parameterized queries throughout

### Role-Based Access Control
- Decorators for role checking (`@super_admin_required`, `@admin_required`)
- Permission decorators (`@permission_required`)
- View-level access control
- Model-level validation

### Audit Logging
- Automatic logging of all user actions
- IP address and user agent tracking
- Detailed action descriptions
- Immutable audit trail

## Usage

### Super Admin Functions
- Create and manage all users
- Assign admin roles
- Grant/revoke permissions
- View audit logs
- Full system access

### Admin Functions
- Create and manage staff users
- Assign permissions to staff
- Cannot promote users to admin
- Cannot access audit logs

### Staff Functions
- Basic system access
- Permissions based on assignments
- Cannot manage other users

## API Endpoints

- `/` - Dashboard
- `/login/` - Login page
- `/logout/` - Logout
- `/users/` - User list
- `/users/create/` - Create user
- `/users/<id>/` - User details
- `/users/<id>/update/` - Update user
- `/users/<id>/delete/` - Delete user
- `/users/<id>/permissions/` - Manage permissions
- `/audit-logs/` - View audit logs

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations inventory
```

### Applying Migrations
```bash
python manage.py migrate
```

### Creating Super Admin
```bash
python manage.py create_superadmin --username <username> --email <email> --password <password>
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository.
