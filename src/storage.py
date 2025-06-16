import json
import os
from typing import Set, Dict, List, Optional
import logging
import redis
from datetime import datetime

logger = logging.getLogger(__name__)


class Storage:
    """Abstract base class for storage backends"""
    
    def add_subscriber(self, chat_id: int) -> None:
        raise NotImplementedError
        
    def remove_subscriber(self, chat_id: int) -> None:
        raise NotImplementedError
        
    def get_subscribers(self) -> Set[int]:
        raise NotImplementedError
        
    def is_subscribed(self, chat_id: int) -> bool:
        raise NotImplementedError
        
    def mark_job_as_seen(self, job_guid: str) -> None:
        raise NotImplementedError
        
    def is_job_seen(self, job_guid: str) -> bool:
        raise NotImplementedError
        
    def get_seen_jobs(self, chat_id: int = None) -> Set[str]:
        raise NotImplementedError
        
    def add_seen_job(self, chat_id: int, job_guid: str) -> None:
        raise NotImplementedError
        
    def set_user_job_type(self, chat_id: int, job_type: str) -> None:
        raise NotImplementedError
        
    def get_user_job_type(self, chat_id: int) -> Optional[str]:
        raise NotImplementedError
        
    def clear_user_job_type(self, chat_id: int) -> None:
        raise NotImplementedError
        
    def add_user_job_type_filter(self, chat_id: int, job_type: str) -> None:
        raise NotImplementedError
        
    def remove_user_job_type_filter(self, chat_id: int, job_type: str) -> None:
        raise NotImplementedError
        
    def get_user_job_type_filters(self, chat_id: int) -> List[str]:
        raise NotImplementedError
        
    def clear_user_job_type_filters(self, chat_id: int) -> None:
        raise NotImplementedError
        
    def add_custom_filter(self, chat_id: int, keyword: str) -> None:
        raise NotImplementedError
        
    def remove_custom_filter(self, chat_id: int, keyword: str) -> None:
        raise NotImplementedError
        
    def get_custom_filters(self, chat_id: int) -> List[str]:
        raise NotImplementedError
        
    def clear_custom_filters(self, chat_id: int) -> None:
        raise NotImplementedError
        
    def save_favorite_job(self, chat_id: int, job_guid: str, job_data: Dict) -> None:
        raise NotImplementedError
        
    def remove_favorite_job(self, chat_id: int, job_guid: str) -> None:
        raise NotImplementedError
        
    def get_favorite_jobs(self, chat_id: int) -> Dict:
        raise NotImplementedError
        
    def get_last_check_time(self) -> Optional[datetime]:
        raise NotImplementedError
        
    def set_last_check_time(self, check_time: datetime) -> None:
        raise NotImplementedError


class FileStorage(Storage):
    """File-based storage for development/small deployments"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.subscribers_file = os.path.join(data_dir, "subscribers.json")
        self.seen_jobs_file = os.path.join(data_dir, "seen_jobs.json")
        self.user_filters_file = os.path.join(data_dir, "user_filters.json")
        
        self._ensure_files_exist()
        
    def _ensure_files_exist(self):
        """Ensure storage files exist"""
        if not os.path.exists(self.subscribers_file):
            self._save_json(self.subscribers_file, [])
            
        if not os.path.exists(self.seen_jobs_file):
            self._save_json(self.seen_jobs_file, [])
            
        if not os.path.exists(self.user_filters_file):
            self._save_json(self.user_filters_file, {})
            
    def _load_json(self, filepath: str) -> list:
        """Load JSON data from file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return [] if filepath != self.user_filters_file else {}
            
    def _save_json(self, filepath: str, data) -> None:
        """Save JSON data to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
            
    def add_subscriber(self, chat_id: int) -> None:
        """Add a subscriber"""
        subscribers = set(self._load_json(self.subscribers_file))
        subscribers.add(chat_id)
        self._save_json(self.subscribers_file, list(subscribers))
        logger.info(f"Added subscriber: {chat_id}")
        
    def remove_subscriber(self, chat_id: int) -> None:
        """Remove a subscriber"""
        subscribers = set(self._load_json(self.subscribers_file))
        subscribers.discard(chat_id)
        self._save_json(self.subscribers_file, list(subscribers))
        logger.info(f"Removed subscriber: {chat_id}")
        
    def get_subscribers(self) -> Set[int]:
        """Get all subscribers"""
        return set(self._load_json(self.subscribers_file))
        
    def is_subscribed(self, chat_id: int) -> bool:
        """Check if user is subscribed"""
        return chat_id in self.get_subscribers()
        
    def mark_job_as_seen(self, job_guid: str) -> None:
        """Mark a job as seen"""
        seen_jobs = set(self._load_json(self.seen_jobs_file))
        seen_jobs.add(job_guid)
        
        # Keep only recent jobs to prevent file from growing too large
        # Keep last 1000 job GUIDs
        seen_jobs_list = list(seen_jobs)
        if len(seen_jobs_list) > 1000:
            seen_jobs_list = seen_jobs_list[-1000:]
            
        self._save_json(self.seen_jobs_file, seen_jobs_list)
        
    def is_job_seen(self, job_guid: str) -> bool:
        """Check if job has been seen"""
        return job_guid in self.get_seen_jobs()
        
    def get_seen_jobs(self, chat_id: int = None) -> Set[str]:
        """Get seen job GUIDs for a specific user or all users"""
        if chat_id is None:
            # Return global seen jobs for backwards compatibility
            return set(self._load_json(self.seen_jobs_file))
        else:
            # Return user-specific seen jobs
            user_seen_file = os.path.join(self.data_dir, f"seen_jobs_{chat_id}.json")
            if os.path.exists(user_seen_file):
                return set(self._load_json(user_seen_file))
            return set()
            
    def add_seen_job(self, chat_id: int, job_guid: str) -> None:
        """Add a seen job for a specific user"""
        user_seen_file = os.path.join(self.data_dir, f"seen_jobs_{chat_id}.json")
        seen_jobs = set()
        
        # Load existing seen jobs if file exists
        if os.path.exists(user_seen_file):
            seen_jobs = set(self._load_json(user_seen_file))
        
        # Add new seen job
        seen_jobs.add(job_guid)
        
        # Keep only recent jobs to prevent file from growing too large
        seen_jobs_list = list(seen_jobs)
        if len(seen_jobs_list) > 1000:
            seen_jobs_list = seen_jobs_list[-1000:]
            
        self._save_json(user_seen_file, seen_jobs_list)
        logger.info(f"Added seen job {job_guid} for user {chat_id}")
        
    def set_user_job_type(self, chat_id: int, job_type: str) -> None:
        """Set job type preference for a user (legacy single filter method)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) not in user_filters:
            user_filters[str(chat_id)] = {}
            
        user_filters[str(chat_id)]["job_type"] = job_type
        self._save_json(self.user_filters_file, user_filters)
        logger.info(f"Set job type filter for user {chat_id}: {job_type}")
        
    def get_user_job_type(self, chat_id: int) -> Optional[str]:
        """Get job type preference for a user (legacy single filter method)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) in user_filters and "job_type" in user_filters[str(chat_id)]:
            return user_filters[str(chat_id)]["job_type"]
        return None
        
    def clear_user_job_type(self, chat_id: int) -> None:
        """Clear job type preference for a user (legacy single filter method)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) in user_filters and "job_type" in user_filters[str(chat_id)]:
            del user_filters[str(chat_id)]["job_type"]
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Cleared job type filter for user {chat_id}")
            
    def add_user_job_type_filter(self, chat_id: int, job_type: str) -> None:
        """Add a job type filter for a user (multiple filters)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) not in user_filters:
            user_filters[str(chat_id)] = {}
            
        if "job_types" not in user_filters[str(chat_id)]:
            user_filters[str(chat_id)]["job_types"] = []
            
        # Add only if not already in the list
        if job_type not in user_filters[str(chat_id)]["job_types"]:
            user_filters[str(chat_id)]["job_types"].append(job_type)
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Added job type filter for user {chat_id}: {job_type}")
        
    def remove_user_job_type_filter(self, chat_id: int, job_type: str) -> None:
        """Remove a job type filter for a user (multiple filters)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if (str(chat_id) in user_filters and 
            "job_types" in user_filters[str(chat_id)] and 
            job_type in user_filters[str(chat_id)]["job_types"]):
            
            user_filters[str(chat_id)]["job_types"].remove(job_type)
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Removed job type filter for user {chat_id}: {job_type}")
        
    def get_user_job_type_filters(self, chat_id: int) -> List[str]:
        """Get all job type filters for a user (multiple filters)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) in user_filters and "job_types" in user_filters[str(chat_id)]:
            return user_filters[str(chat_id)]["job_types"]
        return []
        
    def clear_user_job_type_filters(self, chat_id: int) -> None:
        """Clear all job type filters for a user (multiple filters)"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) in user_filters and "job_types" in user_filters[str(chat_id)]:
            user_filters[str(chat_id)]["job_types"] = []
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Cleared all job type filters for user {chat_id}")
            
    def add_custom_filter(self, chat_id: int, keyword: str) -> None:
        """Add a custom keyword filter for a user"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) not in user_filters:
            user_filters[str(chat_id)] = {}
            
        if "custom_filters" not in user_filters[str(chat_id)]:
            user_filters[str(chat_id)]["custom_filters"] = []
            
        # Add only if not already in the list
        if keyword not in user_filters[str(chat_id)]["custom_filters"]:
            user_filters[str(chat_id)]["custom_filters"].append(keyword)
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Added custom filter for user {chat_id}: {keyword}")
        
    def remove_custom_filter(self, chat_id: int, keyword: str) -> None:
        """Remove a custom keyword filter for a user"""
        user_filters = self._load_json(self.user_filters_file)
        
        if (str(chat_id) in user_filters and 
            "custom_filters" in user_filters[str(chat_id)] and 
            keyword in user_filters[str(chat_id)]["custom_filters"]):
            
            user_filters[str(chat_id)]["custom_filters"].remove(keyword)
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Removed custom filter for user {chat_id}: {keyword}")
        
    def get_custom_filters(self, chat_id: int) -> List[str]:
        """Get all custom keyword filters for a user"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) in user_filters and "custom_filters" in user_filters[str(chat_id)]:
            return user_filters[str(chat_id)]["custom_filters"]
        return []
        
    def clear_custom_filters(self, chat_id: int) -> None:
        """Clear all custom keyword filters for a user"""
        user_filters = self._load_json(self.user_filters_file)
        
        if str(chat_id) in user_filters and "custom_filters" in user_filters[str(chat_id)]:
            user_filters[str(chat_id)]["custom_filters"] = []
            self._save_json(self.user_filters_file, user_filters)
            logger.info(f"Cleared all custom filters for user {chat_id}")

    def save_favorite_job(self, chat_id: int, job_guid: str, job_data: Dict) -> None:
        """Save a job as favorite for a user"""
        favorites_file = os.path.join(self.data_dir, f"favorites_{chat_id}.json")
        favorites = {}
        
        # Load existing favorites if file exists
        if os.path.exists(favorites_file):
            try:
                with open(favorites_file, 'r') as f:
                    favorites = json.load(f)
            except json.JSONDecodeError:
                favorites = {}
        
        # Add new favorite
        favorites[job_guid] = job_data
        
        # Save favorites
        with open(favorites_file, 'w') as f:
            json.dump(favorites, f)
        
        logger.info(f"Saved favorite job {job_guid} for user {chat_id}")
        
    def remove_favorite_job(self, chat_id: int, job_guid: str) -> None:
        """Remove a job from user's favorites"""
        favorites_file = os.path.join(self.data_dir, f"favorites_{chat_id}.json")
        
        # Load existing favorites if file exists
        if os.path.exists(favorites_file):
            try:
                with open(favorites_file, 'r') as f:
                    favorites = json.load(f)
                
                # Remove favorite if exists
                if job_guid in favorites:
                    del favorites[job_guid]
                    
                    # Save favorites
                    with open(favorites_file, 'w') as f:
                        json.dump(favorites, f)
                    
                    logger.info(f"Removed favorite job {job_guid} for user {chat_id}")
            except json.JSONDecodeError:
                pass
                
    def get_favorite_jobs(self, chat_id: int) -> Dict:
        """Get all favorite jobs for a user"""
        favorites_file = os.path.join(self.data_dir, f"favorites_{chat_id}.json")
        
        # Load existing favorites if file exists
        if os.path.exists(favorites_file):
            try:
                with open(favorites_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        
        return {}

    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check time for job updates"""
        last_check_file = os.path.join(self.data_dir, "last_check_time.json")
        
        if os.path.exists(last_check_file):
            try:
                with open(last_check_file, 'r') as f:
                    data = json.load(f)
                    if 'last_check_time' in data:
                        return datetime.fromisoformat(data['last_check_time'])
            except (json.JSONDecodeError, ValueError):
                pass
        
        return None
        
    def set_last_check_time(self, check_time: datetime) -> None:
        """Set the last check time for job updates"""
        last_check_file = os.path.join(self.data_dir, "last_check_time.json")
        
        data = {'last_check_time': check_time.isoformat()}
        
        with open(last_check_file, 'w') as f:
            json.dump(data, f)
        
        logger.info(f"Set last check time: {check_time}")


class RedisStorage(Storage):
    """Redis-based storage for production deployments"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.subscribers_key = "cryptojobs:subscribers"
        self.seen_jobs_key = "cryptojobs:seen_jobs"
        
    def add_subscriber(self, chat_id: int) -> None:
        """Add a subscriber"""
        self.redis_client.sadd(self.subscribers_key, str(chat_id))
        logger.info(f"Added subscriber: {chat_id}")
        
    def remove_subscriber(self, chat_id: int) -> None:
        """Remove a subscriber"""
        self.redis_client.srem(self.subscribers_key, str(chat_id))
        logger.info(f"Removed subscriber: {chat_id}")
        
    def get_subscribers(self) -> Set[int]:
        """Get all subscribers"""
        subscribers = self.redis_client.smembers(self.subscribers_key)
        return {int(sub) for sub in subscribers}
        
    def is_subscribed(self, chat_id: int) -> bool:
        """Check if user is subscribed"""
        return self.redis_client.sismember(self.subscribers_key, str(chat_id))
        
    def mark_job_as_seen(self, job_guid: str) -> None:
        """Mark a job as seen with TTL of 30 days"""
        self.redis_client.setex(
            f"cryptojobs:job:{job_guid}", 
            60 * 60 * 24 * 30,  # 30 days TTL
            "1"
        )
        
    def is_job_seen(self, job_guid: str) -> bool:
        """Check if job has been seen"""
        return self.redis_client.exists(f"cryptojobs:job:{job_guid}") > 0
        
    def get_seen_jobs(self, chat_id: int = None) -> Set[str]:
        """Get seen job GUIDs for a specific user or all users"""
        if chat_id is None:
            # Return global seen jobs for backwards compatibility
            keys = self.redis_client.keys("cryptojobs:job:*")
            return {key.split(":")[-1] for key in keys}
        else:
            # Return user-specific seen jobs
            seen_jobs = self.redis_client.smembers(f"cryptojobs:user:{chat_id}:seen_jobs")
            return set(seen_jobs) if seen_jobs else set()
            
    def add_seen_job(self, chat_id: int, job_guid: str) -> None:
        """Add a seen job for a specific user"""
        self.redis_client.sadd(f"cryptojobs:user:{chat_id}:seen_jobs", job_guid)
        # Set TTL of 30 days to prevent memory issues
        self.redis_client.expire(f"cryptojobs:user:{chat_id}:seen_jobs", 60 * 60 * 24 * 30)
        logger.info(f"Added seen job {job_guid} for user {chat_id}")
        
    def set_user_job_type(self, chat_id: int, job_type: str) -> None:
        """Set job type preference for a user (legacy single filter method)"""
        self.redis_client.hset(f"cryptojobs:user:{chat_id}", "job_type", job_type)
        logger.info(f"Set job type filter for user {chat_id}: {job_type}")
        
    def get_user_job_type(self, chat_id: int) -> Optional[str]:
        """Get job type preference for a user (legacy single filter method)"""
        job_type = self.redis_client.hget(f"cryptojobs:user:{chat_id}", "job_type")
        return job_type
        
    def clear_user_job_type(self, chat_id: int) -> None:
        """Clear job type preference for a user (legacy single filter method)"""
        self.redis_client.hdel(f"cryptojobs:user:{chat_id}", "job_type")
        logger.info(f"Cleared job type filter for user {chat_id}")
        
    def add_user_job_type_filter(self, chat_id: int, job_type: str) -> None:
        """Add a job type filter for a user (multiple filters)"""
        self.redis_client.sadd(f"cryptojobs:user:{chat_id}:job_types", job_type)
        logger.info(f"Added job type filter for user {chat_id}: {job_type}")
        
    def remove_user_job_type_filter(self, chat_id: int, job_type: str) -> None:
        """Remove a job type filter for a user (multiple filters)"""
        self.redis_client.srem(f"cryptojobs:user:{chat_id}:job_types", job_type)
        logger.info(f"Removed job type filter for user {chat_id}: {job_type}")
        
    def get_user_job_type_filters(self, chat_id: int) -> List[str]:
        """Get all job type filters for a user (multiple filters)"""
        filters = self.redis_client.smembers(f"cryptojobs:user:{chat_id}:job_types")
        return list(filters) if filters else []
        
    def clear_user_job_type_filters(self, chat_id: int) -> None:
        """Clear all job type filters for a user (multiple filters)"""
        self.redis_client.delete(f"cryptojobs:user:{chat_id}:job_types")
        logger.info(f"Cleared all job type filters for user {chat_id}")
        
    def add_custom_filter(self, chat_id: int, keyword: str) -> None:
        """Add a custom keyword filter for a user"""
        self.redis_client.sadd(f"cryptojobs:user:{chat_id}:custom_filters", keyword)
        logger.info(f"Added custom filter for user {chat_id}: {keyword}")
        
    def remove_custom_filter(self, chat_id: int, keyword: str) -> None:
        """Remove a custom keyword filter for a user"""
        self.redis_client.srem(f"cryptojobs:user:{chat_id}:custom_filters", keyword)
        logger.info(f"Removed custom filter for user {chat_id}: {keyword}")
        
    def get_custom_filters(self, chat_id: int) -> List[str]:
        """Get all custom keyword filters for a user"""
        filters = self.redis_client.smembers(f"cryptojobs:user:{chat_id}:custom_filters")
        return list(filters) if filters else []
        
    def clear_custom_filters(self, chat_id: int) -> None:
        """Clear all custom keyword filters for a user"""
        self.redis_client.delete(f"cryptojobs:user:{chat_id}:custom_filters")
        logger.info(f"Cleared all custom filters for user {chat_id}")

    def save_favorite_job(self, chat_id: int, job_guid: str, job_data: Dict) -> None:
        """Save a job as favorite for a user"""
        key = f"cryptojobs:favorite:{chat_id}:{job_guid}"
        self.redis_client.set(key, json.dumps(job_data))
        logger.info(f"Saved favorite job {job_guid} for user {chat_id}")
        
    def remove_favorite_job(self, chat_id: int, job_guid: str) -> None:
        """Remove a job from user's favorites"""
        key = f"cryptojobs:favorite:{chat_id}:{job_guid}"
        self.redis_client.delete(key)
        logger.info(f"Removed favorite job {job_guid} for user {chat_id}")
        
    def get_favorite_jobs(self, chat_id: int) -> Dict:
        """Get all favorite jobs for a user"""
        # Get all keys for this user's favorites
        keys = self.redis_client.keys(f"cryptojobs:favorite:{chat_id}:*")
        favorites = {}
        
        # Get all favorite jobs
        for key in keys:
            job_guid = key.split(":")[-1]
            job_data = self.redis_client.get(key)
            if job_data:
                favorites[job_guid] = json.loads(job_data)
        
        return favorites

    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check time for job updates"""
        last_check_str = self.redis_client.get("cryptojobs:last_check_time")
        
        if last_check_str:
            try:
                return datetime.fromisoformat(last_check_str)
            except ValueError:
                pass
        
        return None
        
    def set_last_check_time(self, check_time: datetime) -> None:
        """Set the last check time for job updates"""
        self.redis_client.set("cryptojobs:last_check_time", check_time.isoformat())
        logger.info(f"Set last check time: {check_time}")


def get_storage(redis_url: Optional[str] = None) -> Storage:
    """Factory function to get appropriate storage backend"""
    if redis_url:
        try:
            return RedisStorage(redis_url)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to file storage.")
            
    return FileStorage()