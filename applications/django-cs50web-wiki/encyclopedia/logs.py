import logging

logger = logging.getLogger(__name__)


def log_entry_save(instance, created, **kwargs):
    if created:
        logger.info(f'wiki entry [{instance}] created')
    else:
        logger.info(f'wiki entry [{instance}] updated')



def log_entry_delete(instance, **kwargs):
    logger.info(f'wiki entry [{instance}] deleted')
