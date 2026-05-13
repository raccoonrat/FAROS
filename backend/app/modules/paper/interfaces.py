"""Stable public interface for the paper module."""

from .router import router
from .service import generate_paper
from .storage import *  # noqa: F401,F403
