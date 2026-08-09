import logging
import time

logger = logging.getLogger("govrix.audit")
logging.basicConfig(level=logging.INFO)


def log_decision(user: str, agent_id: str, action: str, allowed: bool, detail: str = "") -> None:
    logger.info(
        "audit ts=%s user=%s agent=%s action=%s allowed=%s detail=%s",
        time.time(), user, agent_id, action, allowed, detail,
    )
