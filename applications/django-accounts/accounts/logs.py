import logging

logger = logging.getLogger(__name__)


def log_proxy_user_save(instance, created, **kwargs):
    if created:
        logger.info(f'proxy user [{instance}] created')
    else:
        logger.info(f'proxy user [{instance}] updated')


def log_proxy_user_delete(instance, **kwargs):
    logger.info(f'proxy user [{instance}] deleted')
