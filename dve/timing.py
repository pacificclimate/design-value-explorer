"""
Context manager for timing a block of code (in with statement).
Calls a logging function with timing messages.

Usage:

```
logger = logging.getLogger(__name__)
with timing("description/label", log=logger.debug):
    # Timing start message logged here
    # ... Code to be timed ...
# Timing end message logged here
```
"""
from contextlib import contextmanager
from time import perf_counter


@contextmanager
def timing(
    description,
    log=None,
    multiplier=1000,
    units="ms",
    # Requirement: `multiplier` * `units` = `1 s`
    start_message="Timing [{description}]: start",
    end_message="Timing [{description}]: end; elapsed {elapsed} {units}",
):
    if log is None:
        yield
        return
    start = perf_counter() * multiplier
    if start_message is not None:
        log(
            start_message.format(
                description=description,
                start=start,
                units=units,
                extra={"item": "timing:start", "description": description},
            )
        )
    yield
    end = perf_counter() * multiplier
    elapsed = end - start
    if end_message is not None:
        log(
            end_message.format(
                description=description,
                start=start,
                end=end,
                elapsed=elapsed,
                units=units,
            ),
            extra={
                "item": "timing:end",
                "description": description,
                "elapsed": elapsed,
                "units": units,
            },
        )
