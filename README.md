# YouTube Dubbing MVP

This is an MVP for a YouTube dubbing service that automatically:
1. Downloads YouTube videos
2. Transcribes the audio
3. Translates the text
4. Generates TTS audio
5. Merges new audio with original video

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Environment Variables

Create a `.env` file with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0