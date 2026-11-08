from typing import Literal

import httpx
from agentecore import tool

from config import AI_API_KEY


API_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"
SITE_URL = "https://www.themoviedb.org/movie"
LANGUAGE = "it-IT"
REGION = "IT"
MAX_LIMIT = 10
OVERVIEW_CHARS = 400
TIMEOUT = 20


def _credentials() -> tuple[dict, dict] | None:
    key = str(AI_API_KEY.get("tmdb") or "").strip()
    if not key:
        return None
    if key.startswith("eyJ"):
        return {"Authorization": f"Bearer {key}"}, {}
    return {}, {"api_key": key}


def _get(path: str, params: dict, credentials: tuple[dict, dict]) -> dict:
    headers, auth_params = credentials
    response = httpx.get(
        f"{API_URL}/{path}",
        params={"language": LANGUAGE, **params, **auth_params},
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _year(date: str | None) -> str | None:
    return date[:4] if date and len(date) >= 4 else None


def _short(text: str | None) -> str:
    text = (text or "").strip()
    if len(text) <= OVERVIEW_CHARS:
        return text
    return text[:OVERVIEW_CHARS].rstrip() + "…"


def _summary(item: dict) -> dict:
    poster = item.get("poster_path")
    return {
        "movie_id": item["id"],
        "title": item.get("title"),
        "original_title": item.get("original_title"),
        "year": _year(item.get("release_date")),
        "rating": item.get("vote_average"),
        "votes": item.get("vote_count"),
        "overview": _short(item.get("overview")),
        "poster": f"{IMAGE_URL}{poster}" if poster else None,
        "url": f"{SITE_URL}/{item['id']}",
    }


def _search(query: str, year: int | None, limit: int, credentials: tuple[dict, dict]) -> dict:
    if not query.strip():
        return {"success": False, "error": "Query mancante."}

    params = {"query": query.strip(), "region": REGION, "include_adult": "false"}
    if year and 1870 <= year <= 2100:
        params["year"] = year

    data = _get("search/movie", params, credentials)
    movies = [_summary(item) for item in (data.get("results") or [])[:limit]]

    return {
        "success": True,
        "query": query.strip(),
        "total_results": data.get("total_results", len(movies)),
        "movies": movies,
        "source": "TMDB",
    }


def _details(movie_id: int | None, credentials: tuple[dict, dict]) -> dict:
    if not movie_id or movie_id <= 0:
        return {"success": False, "error": "movie_id mancante o non valido."}

    try:
        data = _get(f"movie/{movie_id}", {"append_to_response": "credits"}, credentials)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            return {"success": False, "error": f"Film non trovato: {movie_id}"}
        raise

    credits = data.get("credits") or {}
    directors = [
        p["name"] for p in credits.get("crew") or []
        if p.get("job") == "Director" and p.get("name")
    ]
    cast = [p["name"] for p in (credits.get("cast") or [])[:8] if p.get("name")]

    return {
        "success": True,
        **_summary(data),
        "overview": (data.get("overview") or "").strip(),
        "tagline": data.get("tagline") or None,
        "runtime_minutes": data.get("runtime") or None,
        "genres": [g["name"] for g in data.get("genres") or []],
        "directors": directors,
        "cast": cast,
        "source": "TMDB",
    }


@tool
def tmdb(
    action: Literal["search", "details"],
    query: str = "",
    year: int | None = None,
    movie_id: int | None = None,
    limit: int = 5,
):
    """Cerca film su TMDB e ne restituisce i dettagli: titolo, anno, trama, voto,
    generi, durata, cast e regia. Non fornisce link per guardare i film.

    Args:
        action: 'search' cerca film per titolo, 'details' dà i dettagli di un film dato il suo movie_id.
        query: titolo (anche parziale) da cercare. Serve con 'search'.
        year: anno di uscita, per restringere la ricerca.
        movie_id: ID TMDB del film, ottenuto da una ricerca. Serve con 'details'.
        limit: numero massimo di risultati (1-10).
    """
    credentials = _credentials()
    if credentials is None:
        return {"success": False, "error": "Chiave TMDB non configurata: aggiungi 'tmdb' in AI_API_KEY."}

    try:
        if action == "search":
            return _search(query, year, max(1, min(limit, MAX_LIMIT)), credentials)
        return _details(movie_id, credentials)

    except httpx.TimeoutException:
        return {"success": False, "error": "TMDB non ha risposto in tempo."}

    except httpx.HTTPStatusError as error:
        return {"success": False, "error": f"TMDB ha risposto HTTP {error.response.status_code}."}

    except (httpx.HTTPError, ValueError, KeyError) as error:
        return {"success": False, "error": f"Errore durante la richiesta a TMDB: {error}"}
