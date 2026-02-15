# services/video-intention/src/consumer/__init__.py
from .valkey_consumer import ValkeyConsumer

__all__ = ["ValkeyConsumer"]
