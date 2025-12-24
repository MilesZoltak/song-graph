# Song Graph

A web application that analyzes Spotify playlists and visualizes songs on a scatter plot based on tempo and sentiment analysis.

## Features

- Fetch playlist data from Spotify (tracks, audio features, album art)
- Fetch lyrics from Genius API
- Analyze sentiment using Hugging Face transformers
- Visualize songs on a scatter plot (Tempo vs Sentiment)
- Interactive tooltips with album art and song details

## Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- Spotify API credentials
- Genius API access token

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your credentials:
```
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/callback
GENIUS_ACCESS_TOKEN=your-genius-access-token
```

5. Set up Spotify OAuth:
   - Go to https://developer.spotify.com/dashboard
   - Create an app
   - Add redirect URI: `http://127.0.0.1:3000/callback`
   - Copy Client ID and Client Secret to `.env`

6. Get Genius API token:
   - Go to https://genius.com/api-clients
   - Create an API client
   - Copy access token to `.env`

7. Run the backend:
```bash
python -m backend.main
# Or with uvicorn directly:
uvicorn backend.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:5173` in your browser
3. Paste a Spotify playlist URL
4. Click "Process" and wait for the pipeline to complete
5. View the playlist preview and scatter plot visualization

## Project Structure

```
song-graph/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── pipeline.py          # Pipeline orchestration
│   ├── playlist_fetch.py    # Spotify API integration
│   ├── lyrics_fetch.py      # Genius API integration
│   ├── sentiment_analysis.py # Sentiment analysis
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── PlaylistInput.jsx
│   │   │   ├── PlaylistPreview.jsx
│   │   │   └── ScatterPlot.jsx
│   │   └── main.jsx
│   └── package.json
└── playlists/               # JSON storage for processed playlists
```

## API Endpoints

- `POST /api/process-playlist` - Process a Spotify playlist
- `GET /api/playlists` - List all processed playlists
- `GET /api/playlists/{name}` - Get a specific playlist
- `GET /api/health` - Health check

## Notes

- The sentiment analysis model downloads on first run (~250MB)
- Processing a playlist can take 1-2 minutes depending on size
- Playlists are saved as JSON files in the `playlists/` directory

