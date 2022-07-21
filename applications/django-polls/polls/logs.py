import logging

logger = logging.getLogger(__name__)

def log_model_updated(sender, **kwargs):
    logger.info(f"updated model Choice[{kwargs['instance']}]")
