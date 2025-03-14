# Phul Bazar - E-commerce API

Phul Bazar is a Django Rest Framework (DRF) based eCommerce API project that includes product management, cart functionality, order processing, and category management. The project uses JWT authentication via Djoser and provides API documentation with drf_yasg (Swagger).

## Features

- **User Authentication:** JWT-based authentication using Djoser.
- **Product Management:** CRUD operations for products.
- **Category Management:** Organize products into categories.
- **Cart System:** Add, remove, and update items in the cart.
- **Order Processing:** Place orders and manage order details.
- **Swagger API Documentation:** Auto-generated API documentation using drf_yasg.

## Technologies Used

- **Django** - Python Web Framework
- **Django Rest Framework (DRF)** - API development
- **Djoser** - JWT authentication
- **drf_yasg** - Swagger API documentation
- **PostgreSQL / SQLite** - Database

## Installation

### Prerequisites
- Python 3.8+
- Django
- PostgreSQL (optional, default is SQLite)
- Virtual environment (recommended)

### Steps to Set Up

1. **Clone the repository**
   ```sh
   git clone https://github.com/yourusername/phul_bazar.git
   cd phul_bazar
   ```

2. **Create and activate a virtual environment**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the root directory and add the following details:**
   ```ini
   SECRET_KEY=your_secret_key_here
   DEBUG=True 
   DB_NAME=phul_bazar_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432 
   ALLOWED_HOSTS=*
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_email_password
   EMAIL_USE_TLS=True
   ```

5. **Apply migrations**
   ```sh
   python manage.py migrate
   ```

6. **Create a superuser**
   ```sh
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```sh
   python manage.py runserver
   ```

## Authentication

Phul Bazar uses JWT authentication via Djoser. To authenticate:

1. Obtain an access token:
   ```sh
   POST /api/auth/jwt/create/
   {
       "email": "user@example.com",
       "password": "yourpassword"
   }
   ```

2. Use the token in API requests:
   ```sh
   Authorization: Bearer your_access_token
   ```

## API Documentation

Swagger documentation is available at:
```
http://127.0.0.1:8000/swagger/
```

Redoc documentation is available at:
```
http://127.0.0.1:8000/redoc/
```

## License
This project is licensed under the MIT License.

## Contact
For any queries, feel free to reach out to [your email/contact details].

