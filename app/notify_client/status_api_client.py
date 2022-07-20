import os
from app.notify_client import NotifyAdminAPIClient, cache
from flask import current_app

class StatusApiClient(NotifyAdminAPIClient):

    def get_status(self, *params):
        return self.get(url='/_status', *params)

    # @cache.set('live-service-and-organisation-counts', ttl_in_seconds=3600)
    def get_count_of_live_services_and_organisations(self):
        current_app.logger.info("Getting count of live services and organisations")
        current_app.logger.info("Redis url from config is: {}".format(current_app.config['REDIS_URL']))
        current_app.logger.info("Redis url from env is: {}".format( os.environ.get('REDIS_URL') ))
        current_app.logger.info("Redis enabled from config is: {}".format(current_app.config['REDIS_ENABLED']))
        current_app.logger.info("Redis enabled from env is: {}".format( os.environ.get('REDIS_ENABLED') ))
        return self.get(url='/_status/live-service-and-organisation-counts')

    def get_services(self):
        current_app.logger.info("Getting count of live services and organisations")
        current_app.logger.info("Redis url from config is: {}".format(current_app.config['REDIS_URL']))
        current_app.logger.info("Redis url from env is: {}".format( os.environ.get('REDIS_URL') ))
        current_app.logger.info("Redis enabled from config is: {}".format(current_app.config['REDIS_ENABLED']))
        current_app.logger.info("Redis enabled from env is: {}".format( os.environ.get('REDIS_ENABLED') ))
        return self.get(url='/service')


status_api_client = StatusApiClient()
