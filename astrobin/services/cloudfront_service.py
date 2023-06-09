import logging
import random
import string
import time
from typing import List

import boto3

from astrobin.utils import extract_path_from_url

log = logging.getLogger(__name__)


class CloudFrontService:
    def __init__(self, distribution_id: str):
        self.distribution_id = distribution_id
        self.client = boto3.client('cloudfront')

    @staticmethod
    def generate_unique_reference():
        timestamp = str(time.time()).replace('.', '')  # Get the current timestamp without decimals
        random_string = ''.join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )  # Generate a random string
        return timestamp + random_string

    def create_invalidation(self, urls: List[str]):
        if not self.distribution_id:
            return

        return self.client.create_invalidation(
            DistributionId=self.distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(urls),
                    'Items': [extract_path_from_url(x) for x in urls],
                },
                'CallerReference': self.generate_unique_reference()
            }
        )
