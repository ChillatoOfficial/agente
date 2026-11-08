import requests
from agentecore import tool
from config import AI_API_KEY


@tool
def ricerca_web(query: str, max_results: int = 5, search_depth: str = "basic"):
    """
    Cerca informazioni aggiornate su Internet.
    Restituisce titoli, URL, contenuti e fonti
    Usalo per notizie, documentazione, tutorial e ricerche online.
    """
    if not AI_API_KEY["tavily"]:
        return {
            "success": False,
            "error": "Variabile TAVILY_API_KEY non configurata."
        }

    max_results = max(1, min(int(max_results), 10))

    if search_depth not in ("basic", "advanced"):
        search_depth = "basic"
    
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization": f"Bearer {AI_API_KEY['tavily']}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "topic": "general",
                "include_answer": True
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        results = []

        for item in data.get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
                "score": item.get("score"),
                "published_date": item.get("published_date")
            })

        return {
            "success": True,
            "query": query,
            "answer": data.get("answer"),
            "total_results": len(results),
            "results": results
        }

    except requests.Timeout:
        return {
            "success": False,
            "error": "La ricerca ha superato il tempo massimo."
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": f"Errore durante la ricerca: {error}"
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }
