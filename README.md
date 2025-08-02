# TerraMind - Multimodal Emotional Journaling

A comprehensive emotional wellness platform that combines AI-powered analysis with multimodal input support for journaling.

## Project Structure

```
TerraMind/
├── frontend/                 # React TypeScript frontend with Vite
│   ├── src/
│   │   ├── styles/
│   │   │   └── glassmorphism.css  # Glassmorphic design system
│   │   └── ...
│   ├── package.json
│   └── tailwind.config.js    # TailwindCSS with emotional color palette
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Configuration and settings
│   │   ├── db/              # Database connections
│   │   ├── models/          # Data models
│   │   ├── services/        # Business logic
│   │   └── utils/           # Utility functions
│   ├── requirements.txt
│   └── main.py
├── .env.example             # Environment variables template
└── setup-dev.sh            # Development setup script
```

## Quick Start

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd TerraMind
   cp .env.example .env
   # Edit .env with your configuration values
   ```

2. **Run the setup script:**
   ```bash
   ./setup-dev.sh
   ```

3. **Start the development servers:**

   **Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

   **Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Features

- **Glassmorphic Design System**: Beautiful, modern UI with emotional color coding
- **Multimodal Input**: Support for text, audio, and video journaling
- **AI-Powered Analysis**: Emotional state detection and insights
- **Secure Authentication**: User management and data protection
- **Real-time Processing**: Fast, responsive user experience

## Technology Stack

### Frontend
- React 19 with TypeScript
- Vite for fast development
- TailwindCSS with custom glassmorphic design system
- Framer Motion for animations
- React Query for state management

### Backend
- FastAPI with Python 3.11
- Supabase for database and authentication
- Google Gemini AI for emotional analysis
- Async/await for high performance
- Structured logging and error handling

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `SUPABASE_URL` & `SUPABASE_KEY`: Database connection
- `GEMINI_API_KEY`: AI analysis service
- `SECRET_KEY`: Application security
- Frontend variables prefixed with `VITE_`

## Development

The project uses modern development practices:
- TypeScript for type safety
- ESLint for code quality
- Hot reload for both frontend and backend
- Structured project organization
- Environment-based configuration

## Next Steps

After setup, you can begin implementing features by following the task list in `.kiro/specs/multimodal-emotional-journaling/tasks.md`.