# server.py
import uvicorn
from sonarr_calendar.web import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)