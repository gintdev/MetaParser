from pathlib import Path

from loguru import logger as base_logger


_configured_sinks = set()


def get_component_logger(component_name: str, log_path: str, level: str = "INFO"):
    """Return a logger bound to one component and routed only to its file."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    sink_key = (component_name, str(log_file.resolve()))
    if sink_key not in _configured_sinks:
        base_logger.add(
            str(log_file),
            level=level,
            enqueue=True,
            filter=lambda record, component=component_name: record["extra"].get("component") == component,
        )
        _configured_sinks.add(sink_key)

    return base_logger.bind(component=component_name)
