import hashlib
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TMDBService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.timeout = 10
        self.session = self._create_session()
        self._initialized = True
        
        logger.info("TMDBService initialized")

    def _create_session(self):
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _get(self, endpoint, params=None, cache_key=None, cache_timeout=3600):

        if params is None:
            params = {}

        if cache_key:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_data
            logger.debug(f"Cache MISS: {cache_key}")

        params["api_key"] = self.api_key
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"TMDB API success: {endpoint} - Status: {response.status_code}")

            if cache_key:
                cache.set(cache_key, data, timeout=cache_timeout)
                logger.debug(f"Cached: {cache_key} for {cache_timeout}s")

            return data

        except requests.exceptions.HTTPError as e:
            logger.error(f"TMDB HTTP error: {endpoint} - {response.status_code} - {str(e)}")
            
            error_data = {
                "success": False,
                "error": str(e),
                "status_code": response.status_code
            }
            
            if response.status_code >= 500 and cache_key:
                cache.set(cache_key, error_data, timeout=60)
                
            return error_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB request error: {endpoint} - {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_trending_movies(self):
        return self._get(
            "/trending/movie/week",
            cache_key="trending_movies",
            cache_timeout=7200 
        )

    def search_movies(self, query, page=1):
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        cache_key = f"search_{query_hash}_p{page}"
        
        return self._get(
            "/search/movie",
            {"query": query, "page": page},
            cache_key=cache_key,
            cache_timeout=300  
        )

    def get_movie_details(self, movie_id):
        return self._get(
            f"/movie/{movie_id}",
            cache_key=f"movie_{movie_id}",
            cache_timeout=86400 
        )

    def get_movie_credits(self, movie_id):
        return self._get(
            f"/movie/{movie_id}/credits",
            cache_key=f"credits_{movie_id}",
            cache_timeout=86400 
        )

    def get_watch_providers(self, movie_id):
        """Get streaming providers for a movie"""
        return self._get(
            f"/movie/{movie_id}/watch/providers",
            cache_key=f"providers_{movie_id}",
            cache_timeout=43200  
        )

    def get_multiple_movie_details(self, movie_ids):
        results = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_id = {
                executor.submit(self.get_movie_details, movie_id): movie_id 
                for movie_id in movie_ids
            }
            
            for future in as_completed(future_to_id):
                movie_id = future_to_id[future]
                try:
                    data = future.result()
                    results[movie_id] = data
                except Exception as e:
                    logger.error(f"Failed to fetch movie {movie_id}: {e}")
                    results[movie_id] = {"success": False, "error": str(e)}
        
        return results

    def invalidate_movie_cache(self, movie_id):
        cache_keys = [
            f"movie_{movie_id}",
            f"credits_{movie_id}",
            f"providers_{movie_id}",
        ]
        cache.delete_many(cache_keys)
        logger.info(f"Invalidated cache for movie {movie_id}")

    def refresh_movie_data(self, movie_id):
        self.invalidate_movie_cache(movie_id)
        return self.get_movie_details(movie_id)

    def close_session(self):
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("TMDBService session closed")
    
    def __del__(self):
        self.close_session()