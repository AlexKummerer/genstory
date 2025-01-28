# **GenStoryAPI**

## **Introduction Story**

Imagine a world where you can create vibrant characters and compelling stories with just a few clicks. This API empowers writers, educators, and creators to build, manage, and refine characters and stories effortlessly. Whether you're crafting a whimsical fairy tale or an epic adventure, this tool provides the resources to bring your imagination to life.

## **Overview**

The Character and Story API is a comprehensive system for managing characters and stories in a storytelling environment. It supports creating and refining characters, managing story details, and authenticating users for secure operations.

### **Features**

- **Character Management**:
  - Create, update, and manage characters with detailed descriptions, traits, and statuses.
  - Generate optimized traits and story contexts using OpenAI integration.
- **Story Management**:
  - Create and manage story details, including titles, descriptions, and associated characters.
  - Generate enhanced story descriptions and character roles.
  - Support for storing cover images (base64 encoded).
- **User Management and Authentication**:
  - Secure user authentication using FastAPI Users with JWT tokens.
- **Database Migrations**:
  - Manage database schema with Alembic.

---

## **Getting Started**

### **Prerequisites**

- Python 3.9+
- A virtual environment tool (e.g., `venv` or `virtualenv`).
- `pip` for installing dependencies.
- SQLite (default database).

### **Setup**

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create a virtual environment:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables:

   - Create a `.env` file in the root directory with the following content:
     ```env
     DATABASE_URL=sqlite+aiosqlite:///./test.db
     SECRET_KEY=your-secret-key
     OPENAI_API_KEY=your-openai-api-key
     ```

5. Initialize the database:

   ```bash
   python -m app.db.init_db
   ```

6. Run the development server:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Access the API documentation:
   - Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.
   - Visit `http://127.0.0.1:8000/redoc` for the ReDoc documentation.

---

## **Authentication**

### **Overview**

- Uses JWT-based authentication via FastAPI Users.
- Provides secure endpoints for user registration, login, and profile management.

### **Endpoints**

| Method | Endpoint               | Description                          |
| ------ | ---------------------- | ------------------------------------ |
| POST   | `/auth/register`       | Register a new user.                 |
| POST   | `/auth/jwt/login`      | Authenticate and obtain a JWT token. |
| GET    | `/auth/me`             | Get details of the current user.     |
| POST   | `/auth/request-reset`  | Request a password reset token.      |
| POST   | `/auth/reset-password` | Reset the password using a token.    |

### **Example Authentication Header**

Include the JWT token in the `Authorization` header for protected routes:

```http
Authorization: Bearer <your-jwt-token>
```

---

## **Character Management**

### **Endpoints**

| Method | Endpoint                    | Description                                             |
| ------ | --------------------------- | ------------------------------------------------------- |
| POST   | `/characters/`              | Create a new character.                                 |
| POST   | `/characters/{id}/generate` | Generate and refine traits and context for a character. |
| PUT    | `/characters/{id}/save`     | Update character details.                               |
| POST   | `/characters/{id}/finalize` | Finalize a character, preventing further updates.       |
| GET    | `/characters/`              | Fetch all characters (with optional filters).           |
| GET    | `/characters/{id}`          | Fetch details of a specific character by ID.            |
| DELETE | `/characters/{id}`          | Delete a character.                                     |

### **Character Lifecycle**

- Characters can have the following statuses:
  - **Draft**: When initially created.
  - **Generated**: After traits and context are optimized.
  - **Finalized**: Locked, preventing further modifications.

---

## **Story Management**

### **Endpoints**

| Method | Endpoint                 | Description                                                     |
| ------ | ------------------------ | --------------------------------------------------------------- |
| POST   | `/stories/`              | Create a new story.                                             |
| PUT    | `/stories/{id}`          | Update story details.                                           |
| POST   | `/stories/{id}/generate` | Generate and refine enhanced story details and character roles. |
| POST   | `/stories/{id}/cover`    | Generate a cover image for a story.                             |
| GET    | `/stories/`              | Fetch all stories (with optional filters).                      |
| GET    | `/stories/{id}`          | Fetch a specific story by ID.                                   |
| DELETE | `/stories/{id}`          | Delete a story.                                                 |

### **Story Lifecycle**

- Stories can have the following statuses:
  - **Draft**: Initial state with incomplete details.
  - **Generated**: After enhanced details and roles are generated.
  - **Finalized**: Locked, preventing further modifications.
  - **Published**: Ready for public viewing.
  - **Archived**: No longer active but retained for reference.

---

## **Database Migrations**

### **Overview**

This project uses **Alembic** for database migrations to handle schema changes in a structured and version-controlled manner.

### **Setup**

1. **Ensure Alembic is installed**:

   ```bash
   pip install alembic
   ```

2. **Initialize Alembic (if not already done)**:

   - Run the following command to create the `alembic` directory and configuration files:
     ```bash
     alembic init alembic
     ```

3. **Configure the `alembic.ini` file**:

   - Update the `sqlalchemy.url` key with your database URL:
     ```ini
     sqlalchemy.url = sqlite+aiosqlite:///./test.db
     ```

4. **Configure Alembic to work with your models**:

   - In the env.py file, import your Base object and target metadata:
     ```ini
     from app.db.models import Base
     target_metadata = Base.metadata
     ```

### **Using Alembic**

#### **Generate a New Migration**

To create a new migration after making changes to your models:

```bash
alembic revision --autogenerate -m "Description of migration"
```

#### **Apply Migrations**

To apply the migrations and update the database schema:

```bash
alembic upgrade head
```

---

## **Development**

### **Environment Variables**

Ensure the following variables are set in your `.env` file:

```env
DATABASE_URL=sqlite+aiosqlite:///./test.db
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
```

---

## **Contributing**

Contributions are welcome! To add features or report bugs:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Submit a pull request.

---

## **License**

This project is licensed under the MIT License. See `LICENSE` for details.

---

## **Contact**

- Author: Alexander Kummerer
- Email: developer@alexkummerer.de
- GitHub: [https://github.com/AlexKummerer]
- Project Repository: [https://github.com/AlexKummerer/genstory]
