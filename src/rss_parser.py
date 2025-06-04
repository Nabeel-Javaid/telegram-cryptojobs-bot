import feedparser
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Job:
    """Represents a job listing from the RSS feed"""
    
    def __init__(self, title: str, link: str, description: str, 
                 published: str, guid: str = None):
        self.title = title
        self.link = link
        self.description = description
        self.published = published
        self.guid = guid or self._generate_guid()
        self.company = self._extract_company()
        self.clean_description = self._clean_description()
        self.job_type = self._extract_job_type()
        
    def _generate_guid(self) -> str:
        """Generate a unique ID for the job based on title and link"""
        content = f"{self.title}{self.link}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _extract_company(self) -> str:
        """Extract company name from the job link or title"""
        # Example: staff-product-manager-remote-canada-at-shakepay
        match = re.search(r'-at-([^.]+)(?:\.png)?$', self.link)
        if match:
            company = match.group(1).replace('-', ' ').title()
            return company
        return "Unknown Company"
    
    def _extract_job_type(self) -> str:
        """Extract job type from title and description"""
        # Combine title and description for better detection
        content = f"{self.title.lower()} {self.clean_description.lower()}"
        
        # Define job type keywords
        job_types = {
            "fullstack": ["fullstack", "full stack", "full-stack"],
            "frontend": ["frontend", "front end", "front-end", "ui developer", "react developer"],
            "backend": ["backend", "back end", "back-end", "api developer"],
            "mobile": ["mobile", "ios", "android", "flutter", "react native"],
            "devops": ["devops", "dev ops", "sre", "site reliability", "infrastructure"],
            "blockchain": ["blockchain", "smart contract", "solidity", "web3", "crypto", "nft"],
            "ai": ["ai", "artificial intelligence", "machine learning", "ml engineer", "data scientist"],
            "data": ["data engineer", "data analyst", "database", "sql"],
            "design": ["designer", "ui/ux", "ui designer", "ux designer"],
            "product": ["product manager", "product owner"],
            "qa": ["qa", "quality assurance", "test", "tester", "testing"],
        }
        
        # Find matches
        for job_type, keywords in job_types.items():
            for keyword in keywords:
                if keyword in content:
                    return job_type
                    
        # Default job type if no match
        return "other"
        
    def _clean_description(self) -> str:
        """Clean HTML from description and extract meaningful text"""
        soup = BeautifulSoup(self.description, 'html.parser')
        
        # Remove image tags
        for img in soup.find_all('img'):
            img.decompose()
            
        # Remove all links/tags section
        for p in soup.find_all('p'):
            if 'Tags:' in p.text:
                p.decompose()
                
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up extra whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        # Truncate if too long
        if len(text) > 1000:
            text = text[:997] + "..."
            
        return text
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary for storage"""
        return {
            'title': self.title,
            'link': self.link,
            'description': self.description,
            'published': self.published,
            'guid': self.guid,
            'company': self.company,
            'clean_description': self.clean_description,
            'job_type': self.job_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Job':
        """Create a Job instance from dictionary data"""
        job = cls(
            title=data['title'],
            link=data['link'],
            description=data['description'],
            published=data['published'],
            guid=data['guid']
        )
        # Override computed properties if they exist in the data
        if 'company' in data:
            job.company = data['company']
        if 'clean_description' in data:
            job.clean_description = data['clean_description']
        if 'job_type' in data:
            job.job_type = data['job_type']
        return job
    
    def to_telegram_message(self) -> str:
        """Format job for Telegram message"""
        message = f"🆕 <b>{self.title}</b>\n"
        message += f"🏢 <b>Company:</b> {self.company}\n"
        
        # Add job type
        job_type_emoji = {
            "fullstack": "👨‍💻",
            "frontend": "🖌️",
            "backend": "⚙️",
            "mobile": "📱",
            "devops": "🔧",
            "blockchain": "⛓️",
            "ai": "🧠",
            "data": "📊",
            "design": "🎨",
            "product": "📝",
            "qa": "🔍",
            "other": "💼",
        }
        emoji = job_type_emoji.get(self.job_type, "💼")
        message += f"{emoji} <b>Job Type:</b> {self.job_type.title()}\n"
        
        message += f"🔗 <a href='{self.link}'>View Job</a>\n\n"
        
        # Add first few lines of description
        desc_lines = self.clean_description.split('\n')[:5]
        description_preview = '\n'.join(desc_lines)
        if len(desc_lines) > 5 or len(self.clean_description) > 500:
            description_preview += "\n..."
            
        message += f"📝 <b>Description:</b>\n{description_preview}"
        
        return message


class RSSParser:
    """Parses the CryptoJobsList RSS feed"""
    
    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        self._cache = {}  # Cache for recently fetched jobs
        
    def fetch_jobs(self) -> List[Job]:
        """Fetch and parse jobs from the RSS feed"""
        try:
            logger.info(f"Fetching RSS feed from {self.feed_url}")
            feed = feedparser.parse(self.feed_url)
            
            if feed.bozo:
                logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return []
                
            jobs = []
            for entry in feed.entries:
                try:
                    job = Job(
                        title=entry.get('title', 'No Title'),
                        link=entry.get('link', ''),
                        description=entry.get('description', ''),
                        published=entry.get('published', ''),
                        guid=entry.get('guid', '')
                    )
                    jobs.append(job)
                    # Cache job by GUID for later retrieval
                    self._cache[job.guid] = job
                except Exception as e:
                    logger.error(f"Error parsing job entry: {e}")
                    continue
                    
            logger.info(f"Fetched {len(jobs)} jobs from RSS feed")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []
    
    def get_job_by_guid(self, guid: str) -> Optional[Job]:
        """Get a job by its GUID"""
        # Check cache first
        if guid in self._cache:
            return self._cache[guid]
        
        # If not in cache, fetch all jobs and try again
        jobs = self.fetch_jobs()
        for job in jobs:
            if job.guid == guid:
                return job
        
        return None
    
    def get_latest_jobs(self, limit: int = 5, job_type: Optional[str] = None, 
                     job_types: Optional[List[str]] = None, 
                     custom_filters: Optional[List[str]] = None) -> List[Job]:
        """
        Get the latest N jobs from the feed, with optional filtering
        
        Args:
            limit: Maximum number of jobs to return
            job_type: Legacy single job type filter
            job_types: List of job types to include (OR condition)
            custom_filters: List of custom keywords to filter by (OR condition)
        """
        jobs = self.fetch_jobs()
        filtered_jobs = jobs
        
        # Apply job type filters (if any)
        if job_type or job_types:
            # Create a set of all job types to filter by
            filter_types = set()
            if job_type:
                filter_types.add(job_type)
            if job_types:
                filter_types.update(job_types)
                
            # Filter jobs by job type
            if filter_types:
                filtered_jobs = [job for job in filtered_jobs if job.job_type in filter_types]
                logger.info(f"Filtered to {len(filtered_jobs)} jobs by job types: {', '.join(filter_types)}")
        
        # Apply custom keyword filters (if any)
        if custom_filters:
            # Filter jobs by custom keywords (in title or description)
            custom_filtered = []
            for job in filtered_jobs:
                job_content = f"{job.title.lower()} {job.clean_description.lower()}"
                if any(keyword.lower() in job_content for keyword in custom_filters):
                    custom_filtered.append(job)
            
            filtered_jobs = custom_filtered
            logger.info(f"Filtered to {len(filtered_jobs)} jobs by custom filters: {', '.join(custom_filters)}")
            
        return filtered_jobs[:limit]
        
    def get_available_job_types(self) -> List[str]:
        """Get all available job types from the current feed"""
        jobs = self.fetch_jobs()
        job_types = sorted(set(job.job_type for job in jobs))
        return job_types