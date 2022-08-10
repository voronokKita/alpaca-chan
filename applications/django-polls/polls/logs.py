import logging

logger = logging.getLogger(__name__)


def log_choice_save(instance, created, **kwargs):
    if created is False:
        logger.info(f'question [{instance.question}] choice [{instance}] updated')
