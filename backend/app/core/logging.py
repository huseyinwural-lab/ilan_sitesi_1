
import structlog
import logging
import sys
import os
from asgi_correlation_id import correlation_id

def configure_logging():
    json_logs = os.environ.get("LOG_FORMAT", "json") == "json"
    
    # Processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add Correlation ID
    def add_correlation(logger, log_method, event_dict):
        req_id = correlation_id.get()
        if req_id:
            event_dict["request_id"] = req_id
        return event_dict

    shared_processors.insert(0, add_correlation)

    if json_logs:
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Stdlib Interception
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Replace handlers
    root_logger = logging.getLogger()
    # root_logger.handlers = [] # Keep basic for now to avoid losing logs if structlog fails init
    # ideally we wrap existing logs. structlog.stdlib.LoggerFactory handles it via structlog.get_logger
    
    # But for libraries using logging.getLogger(), we need a formatter if we want JSON
    # For MVP Stabilization, we'll focus on App Logs using structlog
    pass
