# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GenStoryAI is a FastAPI-based backend for AI-powered story generation. It allows users to create, manage, and refine characters and stories with OpenAI integration. Currently focused on children's stories (ages 6-10) but designed to be scalable to other target audiences.

## Development Commands

### Running the Application
```bash
# Start development server with hot reload
uvicorn app.main:app --reload

# Access API documentation
# Swagger UI: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc
```

### Database Operations
```bash
# Initialize database
python -m app.db.init_db

# Create new migration after model changes
alembic revision --autogenerate -m "Description of migration"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1
```

### Environment Setup
```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Required .env variables
DATABASE_URL=sqlite+aiosqlite:///./test.db
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
```

## Architecture Patterns

### Service Layer Pattern
The application uses a service layer pattern to separate business logic from API endpoints:
- **API Routes** (`app/api/`): Handle HTTP requests/responses, authentication, and validation
- **Services** (`app/services/`): Contain business logic, database operations, and AI integrations
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation

Example flow: API endpoint → Service method → Database/AI operations → Response schema

### Authentication System
Uses FastAPI-Users with JWT tokens:
- User management handled in `app/users/user.py`
- Protected endpoints use `Depends(active_user)` dependency
- JWT tokens expire after 3600 seconds (1 hour)
- Authentication backend: Bearer token transport with JWT strategy

### AI Integration Architecture
The system supports multiple AI providers:
- **Primary**: OpenAI (`app/utils/openai_client.py`) - used for all generation
- **Alternative**: Groq and Grok clients available but not currently integrated
- Structured prompts use Pydantic models for type safety
- Generation flow: Character/Story data → Structured prompt → AI API → Parsed response

### Database Relationships
```
User (1) ──→ (N) Character
User (1) ──→ (N) Story
Story (N) ←─→ (N) Character (via character_ids JSON field)
Story (1) ──→ (0,1) Image
```

### Status Workflows
Both Characters and Stories follow a status progression:
- **Character**: draft → generated → finalized
- **Story**: draft → generated → finalized → published → archived

## Key Implementation Details

### Story Generation Process
1. User creates characters with traits and descriptions
2. Characters must be in 'generated' or 'finalized' status to use in stories
3. Story creation requires character IDs
4. Story refinement generates optimized title, description, and character roles
5. Content generation creates full story structure with lessons
6. Cover image generation uses DALL-E 3 based on story content

### Current Target Audience Limitation
The system is hardcoded for children's stories in several places:
- `app/utils/openai_client.py:179`: System prompt specifies "children's stories"
- `app/utils/openai_client.py:463`: Story prompt targets "children aged 6-10"
- `app/utils/openai_client.py:217-218`: Cover image prompt mentions "child" audience

To scale to other audiences, these prompts need to be parameterized based on story type/audience.

### API Endpoint Structure
- `/auth/*`: Authentication endpoints (register, login, password reset)
- `/characters/*`: Character CRUD and generation
- `/stories/*`: Story CRUD, content generation, and cover images
- `/users/*`: User profile management

### Error Handling Pattern
Services throw exceptions that are caught by API endpoints and converted to HTTP responses:
```python
try:
    return await ServiceClass.method()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error message: {str(e)}")
```

## Testing Approach
Currently no test suite is implemented. When adding tests:
- Use pytest for testing framework
- Test files should follow `test_*.py` or `*_test.py` naming
- Mock external API calls (OpenAI, image generation)
- Use AsyncSession for database testing

## Common Development Tasks

### Adding New Story Types/Audiences
1. Add audience/genre field to Story model
2. Create prompt templates in `app/utils/prompts/`
3. Modify generation functions to use appropriate templates
4. Update schemas to include audience selection
5. Run database migration for model changes

### Modifying AI Prompts
All AI prompts are in `app/utils/openai_client.py`:
- `structured_char_prompt()`: Character generation
- `structured_story_prompt()`: Story details refinement  
- `story_content_prompt()`: Full story generation
- `generate_cover_image_prompt()`: Cover image prompt generation

### Database Schema Changes
1. Modify models in `app/db/models.py`
2. Update corresponding schemas in `app/schemas/`
3. Generate migration: `alembic revision --autogenerate -m "description"`
4. Review generated migration file
5. Apply migration: `alembic upgrade head`

## Project Contact
- Author: Alexander Kummerer
- Email: developer@alexkummerer.de
- Repository: https://github.com/AlexKummerer/genstory