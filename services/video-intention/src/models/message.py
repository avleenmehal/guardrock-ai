from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from marshmallow.utils import timestamp


@dataclass
class VideoMessage:
    """Message received from Valkey queue"""
    uuid: str
    url: str
    title: str
    channel_name: str
    description: str
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoMessage':
        """Create VideoMessage from dictionary"""
        return cls(
            uuid=data['uuid'],
            url=data['url'],
            title=data['title'],
            channel_name=data['channel_name'],
            description=data['description'],
            timestamp=data['timestamp']
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'uuid': self.uuid,
            'url': self.url,
            'title': self.title,
            'channel_name': self.channel_name,
            'description': self.description
        }