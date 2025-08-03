# CliniMatch: AI-Powered Clinical Trial Matching

CliniMatch is a full-stack web application designed to bridge the gap between patients and clinical trials. Finding and understanding clinical trials can be a daunting process, filled with complex medical jargon. CliniMatch simplifies this by using AI to translate trial information into clear, understandable language, and provides a user-friendly platform to find relevant trials based on a user's health profile.

## ✨ Features

- **AI-Powered Translation**: Leverages Google's Gemini AI to translate complex eligibility criteria and trial descriptions into simple, patient-friendly language.
- **Intelligent Trial Matching**: Matches users to relevant clinical trials based on their medical conditions, age, location, and more.
- **Interactive Map View**: Visualizes trial locations on an interactive map using React Leaflet.
- **User-Friendly Interface**: A clean and modern UI built with React, TypeScript, and Tailwind CSS.
- **Secure User Authentication**: Manages user accounts and authentication using Supabase.
- **Robust Backend**: A powerful Flask backend that handles the core logic, including communication with the ClinicalTrials.gov API and the Gemini AI API.
- **Performance Optimized**: Caches trial search results to provide a fast and responsive user experience.

## 🚀 Tech Stack

**Frontend:**
- **Framework**: React, TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Mapping**: React Leaflet
- **Routing**: React Router
- **Authentication**: Supabase Client

**Backend:**
- **Framework**: Flask
- **Language**: Python
- **Database/Cache**: Supabase (PostgreSQL)
- **AI**: Google Gemini API
- **API Communication**: ClinicalTrials.gov API
- **Dependencies**: Flask-CORS, python-dotenv, requests, marshmallow

## 🏁 Getting Started

### Prerequisites

- Node.js and npm (for frontend)
- Python 3.x and pip (for backend)
- A Supabase account (for database/cache and auth)
- A Google Gemini API key

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/clinimatch.git
    cd clinimatch/backend
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the `backend` directory and add the following:
    ```
    FLASK_ENV=development
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_service_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

4.  **Set up the database:**
    Run the database setup script to test your connection to Supabase. This will also provide the SQL schema that you need to run in your Supabase SQL editor to create the necessary tables.
    ```bash
    python setup_database.py
    ```
    Copy the SQL output and execute it in the Supabase SQL Editor for your project.

5.  **Run the backend server:**
    ```bash
    flask run --port 5001
    ```
    The backend API will be running at `http://localhost:5001`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the `frontend` directory and add your Supabase public key:
    ```
    REACT_APP_SUPABASE_URL=your_supabase_url
    REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
    ```

4.  **Run the frontend development server:**
    ```bash
    npm start
    ```
    The application will be available at `http://localhost:3000`.

## ⚙️ API Endpoints

The backend provides the following API endpoints under the `/api` prefix:

- `GET /health`: Health check for the service and its dependencies.
- `POST /match`: The primary endpoint for trial matching. Takes a user profile and returns a list of matching trials.
- `GET /trial/<nct_id>`: Retrieves detailed information for a specific trial by its NCT ID.

### Example `/match` Request Body

```json
{
  "age": 45,
  "conditions": ["Type 2 Diabetes"],
  "medications": ["Metformin"],
  "location": {
    "city": "New York",
    "state": "NY",
    "country": "United States"
  }
}
```