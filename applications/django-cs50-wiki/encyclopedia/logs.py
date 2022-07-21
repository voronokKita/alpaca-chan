import logging

logger = logging.getLogger(__name__)


def log_model_create_or_update(sender, **kwargs):
    if kwargs['created']: s = 'created'
    else: s = 'updated'
    logger.info(f"{s} {sender} [{kwargs['instance']}]")


def log_model_delete(sender, **kwargs):
    logger.info(f"deleted {sender} [{kwargs['instance']}]")
