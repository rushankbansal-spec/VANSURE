"""Celery application configuration and tasks for VanSure backend."""

from __future__ import annotations

from typing import Any

from celery import Celery, Task
from celery.signals import task_postrun, task_prerun

from app.core.config import Settings, get_settings
from app.core.logging import logger


class ContextTask(Task):
    """Task base class with context support."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute task with context setup."""
        logger.info(f"Executing task {self.name}")
        return self.run(*args, **kwargs)


def create_celery_app(settings: Settings | None = None) -> Celery:
    """Create and configure Celery application.

    Args:
        settings: Application settings

    Returns:
        Configured Celery application
    """
    settings = settings or get_settings()

    # Get Redis URL from settings
    redis_url = f"redis://{settings.redis.dsn.host}:{settings.redis.dsn.port or 6379}/0"

    celery_app = Celery(
        "vansure",
        broker=redis_url,
        backend=redis_url.replace("/0", "/1"),  # Separate DB for results
        include=[
            "app.workers.tasks.auth",
            "app.workers.tasks.trips",
            "app.workers.tasks.notifications",
            "app.workers.tasks.billing",
        ],
    )

    # Configure Celery
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutes
        task_soft_time_limit=240,  # 4 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_concurrency=4,
    )

    # Set the base task class
    celery_app.Task = ContextTask

    return celery_app


# Create Celery app instance
celery_app = create_celery_app()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def health_check_task(self) -> dict[str, Any]:
    """Health check task for testing."""
    return {"status": "healthy", "task_id": self.request.id}


# Task registry
__all__ = ["celery_app", "create_celery_app", "ContextTask"]