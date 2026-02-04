## Mark 1 – Neural Engine (Movie Recommender)

Mark 1 is a lightweight movie and TV show recommendation engine powered by The Movie Database (TMDB) API.  
It learns your taste from a few titles you mark as “watched” and then generates **neural-style recommendations** with confidence scores, optimized for fast responses on a Mac M-series machine.

---

### Features

- **Trending overview**: See what’s trending across movies and TV in a clean, modern grid UI.
- **Smart search**: Type to search TMDB and quickly add items to your “watched” profile.
- **Neural-style recommendations**:
  - Infers your **genre preferences** from watched titles.
  - Combines **ratings**, **genre overlap**, and **local neighborhood recommendations** to score candidates.
  - Outputs a **0–100% match score** badge on each recommendation.
- **Streaming availability (India)**: Shows where a title is available to stream in India using TMDB “watch/providers”.
- **Fast & parallelized backend**:
  - Reuses a single HTTP session (TCP keep-alive).
  - Uses `ThreadPoolExecutor` to parallelize TMDB calls.
- **Simple deployment**: Flask app with `gunicorn` and a `Procfile`, ready for platforms like Render/Heroku.

---

### Tech Stack

- **Backend**: Python, Flask
- **Frontend**: Vanilla HTML, CSS, JavaScript (single-page template)
- **HTTP / Data**: `requests`, TMDB API
- **Concurrency**: `concurrent.futures.ThreadPoolExecutor`
- **Other**: `numpy` (for numeric work, if needed), `gunicorn` (for production serving)

---

### Project Structure

```text
.
├── app.py              # Flask backend with TMDB integration and recommendation logic
├── requirements.txt    # Python dependencies
├── Procfile            # Process type definition for production (gunicorn)
└── templates/
    └── index.html      # Main UI (search, grid, sidebar, modal)
```

---

### Prerequisites

- Python 3.9+ recommended
- A TMDB API key (free to obtain)

Create an account and API key at: `https://www.themoviedb.org/`

---

### Configuration

In `app.py` you’ll see:

```python
API_KEY = "your_api_key_here"
```

For security, you should **replace this with your own key** and avoid committing real keys to public repos.  
A safer pattern is to load from an environment variable:

```python
import os

API_KEY = os.getenv("TMDB_API_KEY", "")
```

Then set `TMDB_API_KEY` in your environment before running:

```bash
export TMDB_API_KEY="your_real_tmdb_api_key_here"
```

---

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/<your-username>/Mark1-neural-engine-Movies.git
cd Mark1-neural-engine-Movies-main
```

2. **Create and activate a virtual environment (optional but recommended)**

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
# or on Windows:
# venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

---

### Running Locally (Development)

1. Ensure your TMDB API key is configured (see **Configuration** section).
2. Start the Flask development server:

```bash
python app.py
```

By default the app runs on:

- `http://127.0.0.1:5001/`

Open this URL in your browser.

---

### Running with Gunicorn (Production-style)

With dependencies installed and `TMDB_API_KEY` set:

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 4 --threads 4
```

Or, if your platform honors the `Procfile`, it may automatically run:

```text
web: gunicorn app:app
```

---

### How It Works (High Level)

- **Trending feed**: `/get_trending`
  - Calls TMDB’s `/trending/all/day` endpoint.
  - Normalizes items into a unified format (title, type, rating, year, poster, overview).

- **Profile building**:
  - From the UI, you search and add items to the **watched** sidebar.
  - The list of watched items is sent to `/get_recommendations`.

- **Recommendation engine**: `/get_recommendations`
  - Fetches detailed info (genres, ratings, providers) via a **consolidated TMDB call** using `append_to_response=watch/providers`.
  - Builds a **genre preference profile** using `collections.Counter`.
  - Fetches neighbor recommendations for your last few watched titles.
  - Scores each candidate:
    - Base score from vote average.
    - Bonus for overlapping genres with your profile.
    - Capped at 100.
  - Returns top results with:
    - Match score
    - Overview
    - Poster URL
    - Streaming info for India.

- **Search autosuggest**: `/search`
  - Uses TMDB’s `search/multi` endpoint.
  - Filters to movies/TV with posters and displays a compact suggestion list.

---

### Frontend UX

- **Search bar**: Type to search; suggestions appear with mini posters and an `+ ADD` button.
- **Watched sidebar**:
  - Slide-out panel listing your watched items.
  - Remove items to update your profile dynamically.
- **Movie grid**:
  - Displays either **Trending** or **Neural Recommendations**.
  - Hover and click to see details or add items.
  - Recommendation cards show a **Neural % badge** when scored.
- **Details modal**:
  - Shows title, overview, and streaming availability (India).

---

### Environment & Notes

- This project is optimized for quick responses on macOS (M-series) using:
  - Persistent HTTP session (`requests.Session`) for TCP keep-alive.
  - Thread pools for concurrent TMDB calls.
- The recommendation logic is intentionally **simple and explainable**, ideal as a base for:
  - Experimenting with more advanced similarity metrics.
  - Integrating embeddings or ML models.
  - Expanding beyond India-specific streaming info.

---

### Future Improvements (Ideas)

- Replace simple genre/rating scoring with:
  - Embedding-based similarity.
  - Collaborative filtering.
- Add pagination and infinite scroll for large result sets.
- Support multiple regions for streaming providers.
- Persist user profiles (database or auth-based accounts) instead of in-memory lists.
- Add tests and CI for robustness.

---

### License

Add your preferred license here (e.g. MIT). For example:

```text
MIT License – see LICENSE file for details.
```
