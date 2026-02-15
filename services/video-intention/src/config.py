import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class TwelveLabsConfig:
    """Twelve Labs API configuration"""
    api_key: str
    base_url: str
    index_id: str


@dataclass
class FactCheckerConfig:
    """Fact Checker service configuration"""
    api_url: str
    timeout: int = 5


@dataclass
class ServiceConfig:
    """General service configuration"""
    video_length_limit: int = 15  # seconds
    poll_interval: int = 30  # seconds
    max_concurrent: int = 5


class Config:
    """Main configuration class that loads all configs"""

    def __init__(self):

        self.twelve_labs = TwelveLabsConfig(
            api_key=os.getenv('TWELVE_LABS_API_KEY', ''),
            base_url=os.getenv('TWELVE_LABS_BASE_URL', 'https://api.twelvelabs.io/v1.2'),
            index_id=os.getenv('TWELVE_LABS_INDEX_ID', '')
        )

        self.fact_checker = FactCheckerConfig(
            api_url=os.getenv('FACT_CHECKER_API_URL', 'http://localhost:8080/api/fact-check'),
            timeout=int(os.getenv('FACT_CHECKER_TIMEOUT', '5'))
        )


# Global config instance
config = Config()