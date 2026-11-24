# Architecture

React + TypeScript frontend -> FastAPI REST API -> detection service -> SQLite history.

SMS analysis combines transparent keyword/rule signals with an optional TF-IDF + Logistic
Regression model. URL analysis uses static string/hostname checks only; it does not fetch,
resolve, crawl or open submitted URLs.

# Limitations
- Scores are heuristic indicators, not calibrated fraud probabilities.
- A low score is not proof of safety.
- Demo training data is tiny and illustrative.
- No authentication, rate limiting, production threat-feed integration or formal multilingual
  evaluation is included.
