import redis
import pickle
import logging
from hashlib import md5
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_REDIS_URL='redis://127.0.0.1:6379/1' #TODO: relocate this

REDIS_URL = getattr(settings, 'REDIS_URL', DEFAULT_REDIS_URL)
redis_client = redis.StrictRedis.from_url(REDIS_URL)
CACHE_TIMEOUT = 3600 * 24  # Cache timeout of 1 day

def generate_cache_key(params):
    """
    Generate a unique cache key based on the request parameters
    """
    key_string = str(params)
    return md5(key_string.encode('utf-8')).hexdigest()

def get_cache(key):
    cached_data = redis_client.get(key)
    if cached_data:
        logger.info(f"Cache hit for key: {key}")
        return pickle.loads(cached_data)
    logger.info(f"No cache found for key: {key}")
    return None

def set_cache(key, value, timeout=CACHE_TIMEOUT):
    pickled_data = pickle.dumps(value)
    redis_client.setex(key, timeout, pickled_data)
    logger.info(f"Data cached with key: {key}")
