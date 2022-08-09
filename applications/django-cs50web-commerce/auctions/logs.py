import logging

logger = logging.getLogger(__name__)


def log_profile_save(instance, created, update_fields=None, **kwargs):
    if created:
        logger.info(f'profile [{instance}] created')
    elif 'money' in update_fields:
        logger.info(f'profile [{instance}] money changed, now has {instance.money} coins')


def log_profile_deleted(instance, **kwargs):
    logger.info(f'profile [{instance}] deleted')


def log_category_save(instance, created, **kwargs):
    if created:
        logger.info(f'category [{instance}] created')


def log_bid_save(instance, created, update_fields=None, **kwargs):
    if created:
        logger.info(f'bid from [{instance.auctioneer}], on [{instance.lot}]')


def log_listing_save(instance, created, update_fields=None, **kwargs):
    if created:
        logger.info(f'listing [{instance}] created')
    elif 'owner' in update_fields:
        logger.info(f'listing [{instance}] owner changed to [{instance.owner}]')
