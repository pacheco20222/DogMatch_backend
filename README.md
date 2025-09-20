# DogMatch Backend - First Partial Project

## Project Overview
- Course: Programacion de Dispositivos Moviles SIS3403
- Project: DogMatch backend for a "Tinder for Dogs" style mobile app
- Scope (first partial): Backend only, built with Flask, MySQL, JWT authentication, deployed on Render
- Deliverables: Public GitHub repo, live Render deployment, Postman/Insomnia tests, Trello board, 5-minute demo video, supporting PDF

## Product Concept
DogMatch helps dog owners, shelters, and administrators connect. Users can create dog profiles, swipe on potential matches, chat when both parties agree, browse adoption listings, and discover community events such as meetups or training workshops.

## User Roles
- Standard Owner: manages dogs, performs swipes, chats with matches, joins events
- Shelter or NGO: lists adoptable dogs, responds to adoption interest, hosts events
- Administrator: moderates profiles and reports, oversees metrics, manages events

## Content and Features
- User accounts with secure authentication
- Dog profiles with photos, personality tags, and availability status
- Swipe-based discovery and match creation
- Match messages (future real-time chat with Socket.IO)
- Adoption workflows and contact tracking
- Event catalog with registration and optional payments

## Course Requirement Checklist
1. Objective: social and adoption platform for dogs
2. Users: owner, shelter/NGO, administrator
3. Content: profiles, matches, chat, adoption listings, events
4. Database and CRUD: MySQL tables for users, dogs, photos, matches, messages, events, registrations with full CRUD in Flask
5. Requirements management: user stories tracked in Trello Kanban board
6. Testing: manual API tests in Postman/Insomnia plus pytest suites
7. Deployment: backend hosted on Render with environment variables and migrations applied
8. GitHub: public repository with documented code
9. Delivery: YouTube demo video and PDF covering objectives, users, content, database design

## Technology Stack
- Python 3.x, Flask, SQLAlchemy, Flask-Migrate, Marshmallow
- MySQL (cloud provider such as PlanetScale, Render MySQL, Railway)
- JWT auth with Flask-JWT-Extended or similar
- bcrypt or werkzeug.security for password hashing
- Optional future enhancements: Redis cache, Flask-SocketIO for live chat

## Backend Architecture
```
dogmatch-backend/
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- models/
|   |   |-- __init__.py
|   |   |-- user.py
|   |   |-- dog.py
|   |   |-- match.py
|   |   |-- message.py
|   |   |-- event.py
|   |   `-- event_registration.py
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- users.py
|   |   |-- dogs.py
|   |   |-- matches.py
|   |   |-- messages.py
|   |   `-- events.py
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- auth_utils.py
|   |   |-- db_utils.py
|   |   `-- validators.py
|   `-- static/
|       `-- uploads/
|-- tests/
|-- requirements.txt
|-- run.py
|-- .env
|-- .gitignore
`-- README.md
```

## Data Model Overview
- users: id, email, password_hash, username, user_type, is_active, created_at, updated_at
- dogs: id, owner_id, name, age, breed, gender, size, personality, description, location, is_available, created_at, updated_at
- photos: id, dog_id, url, is_primary, created_at
- matches: id, dog_one_id, dog_two_id, status, matched_at, created_at
- messages: id, match_id, sender_user_id, content, sent_at, is_read
- events: id, organizer_id, title, description, event_date, location, price, max_participants, created_at, updated_at
- event_registrations: id, event_id, user_id, dog_id, registration_date, payment_status

## Authentication and Authorization
- JWT access tokens (15-30 minutes) and refresh tokens (7-30 days)
- Password hashing with bcrypt or werkzeug.security
- Token revocation/blacklist storage (database table or Redis in the future)
- Role-based authorization for admin-only endpoints
- Request validation through Marshmallow schemas

## API Roadmap
- Auth: POST /api/auth/register, POST /api/auth/login, POST /api/auth/refresh, POST /api/auth/logout
- Users: CRUD for profiles, admin moderation endpoints
- Dogs: CRUD for dog profiles, photo metadata uploads
- Matches: swipe actions, match listing, status updates
- Messages: list/create messages for matches (REST placeholder before real-time)
- Events: CRUD for events, registration endpoints, attendee listing

## Security, Testing, and Quality
- Enforce HTTPS in production (Render setup)
- Sanitize and validate incoming payloads
- Mitigate SQL injection through SQLAlchemy ORM usage
- Add pytest-based unit/integration tests (auth, dogs, events)
- Maintain Postman/Insomnia collections for regression testing

## Deployment Plan
1. Configure environment variables (.env locally, Render dashboard in production)
2. Initialize database and run Flask-Migrate migrations
3. Define Render build command (`pip install -r requirements.txt`) and start command (`gunicorn run:app` or equivalent)
4. Test key endpoints after deployment and document results

## Project Management
- User stories grouped by epic (Authentication, Dog Profiles, Matching, Events)
- Trello (or similar) board with Backlog, To Do, In Progress, Testing, Done columns
- Track documentation, deployment, and testing tasks alongside features

## Learning Objectives
- Build a Flask REST API with JWT authentication
- Design relational data models in MySQL and manage migrations
- Practice clean architecture patterns (services, repositories, schemas)
- Deploy and operate a Flask backend on Render
- Apply agile practices (user stories, Kanban) and produce supporting documentation

## Future Enhancements
- Real-time chat with Flask-SocketIO and Redis
- Match recommendations based on breed, location, and preferences
- External photo storage using S3 or similar
- Push notifications via Firebase Cloud Messaging
- Analytics dashboards for administrators

## Reference Links
- Flask documentation: https://flask.palletsprojects.com/
- SQLAlchemy documentation: https://docs.sqlalchemy.org/
- Marshmallow documentation: https://marshmallow.readthedocs.io/
- JWT overview: https://jwt.io/
- Render documentation: https://render.com/docs

---

This README describes the first-partial backend scope. Update it as features move from planning to implementation.
