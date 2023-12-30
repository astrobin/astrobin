import logging
from typing import Optional

import requests
from django.conf import settings

from astrobin.services.utils_service import UtilsService

logger = logging.getLogger(__name__)


class MailingListService:
    api_root = 'https://api.brevo.com/v3'

    def __init__(self, user):
        self.user = user
        self.api_key = settings.BREVO_API_KEY

    def _get_headers(self) -> dict:
        return {
            'api-key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    @staticmethod
    def _is_not_found(response: requests.Response) -> bool:
        if response is None:
            return True

        json = response.json()
        return 'code' in json and json['code'] == 'document_not_found'

    def get_contact(self) -> Optional[requests.Response]:
        try:
            logger.debug('Getting user %s from Brevo', self.user.email)
            response: requests.Response = UtilsService.http_with_retries(
                self.api_root + f'/contacts/{self.user.email}',
                headers=self._get_headers(),
                method='GET'
            )
            logger.debug('Response from Brevo: %s', response.json())
            return response
        except Exception as e:
            logger.error('Error getting user from Brevo: %s', e)
            return None

    def create_contact(self) -> requests.Response:
        try:
            logger.debug('Creating user %s in Brevo', self.user.email)
            response: requests.Response = UtilsService.http_with_retries(
                self.api_root + f'/contacts',
                headers=self._get_headers(),
                method='POST',
                json={
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name
                }
            )
            logger.debug('Response from Brevo: %s', response.json())

            return response
        except Exception as e:
            logger.error('Error creating user in Brevo: %s', e)

    def delete_contact(self) -> requests.Response:
        try:
            logger.debug('Deleting user %s from Brevo', self.user.email)
            response: requests.Response = UtilsService.http_with_retries(
                self.api_root + f'/contacts/{self.user.email}',
                headers=self._get_headers(),
                method='DELETE'
            )
            return response
        except Exception as e:
            logger.error('Error deleting user from Brevo: %s', e)

    def subscribe(self, list_id: int):
        try:
            response: Optional[requests.Response] = self.get_contact()

            if self._is_not_found(response):
                self.create_contact()

            logger.debug('Subscribing user %s to mailing list %s', self.user.email, list_id)
            response: requests.Response = UtilsService.http_with_retries(
                self.api_root + f'/contacts/lists/{list_id}/contacts/add',
                headers=self._get_headers(),
                method='POST',
                json={
                    'emails': [self.user.email]
                }
            )
            logger.debug('Response from Brevo: %s', response.json())
        except Exception as e:
            logger.error('Error subscribing user to mailing list: %s', e)

    def unsubscribe(self, list_id: int):
        try:
            response: Optional[requests.Response] = self.get_contact()

            if self._is_not_found(response):
                return

            logger.debug('Getting user %s from Brevo', self.user.email)
            response: requests.Response = UtilsService.http_with_retries(
                self.api_root + f'/contacts/{self.user.email}',
                headers=self._get_headers(),
                method='GET'
            )
            logger.debug('Response from Brevo: %s', response.json())

            logger.debug('Unsubscribing user %s from mailing list %s', self.user.email, list_id)
            response: requests.Response = UtilsService.http_with_retries(
                self.api_root + f'/contacts/lists/{list_id}/contacts/remove',
                headers=self._get_headers(),
                method='POST',
                json={
                    'emails': [self.user.email]
                }
            )
            logger.debug('Response from Brevo: %s', response.json())
        except Exception as e:
            logger.error('Error subscribing user to mailing list: %s', e)
