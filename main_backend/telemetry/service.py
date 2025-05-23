import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from posthog import Posthog

from main_backend.telemetry.views import BaseTelemetryEvent
from main_backend.utils import singleton

load_dotenv()


logger = logging.getLogger(__name__)


POSTHOG_EVENT_SETTINGS = {
	'process_person_profile': True,
	'geoip_city_name': None,
	'geoip_country_name': None,
	'geoip_country_code': None,
	'geoip_continent_name': None,
	'geoip_continent_code': None,
	'geoip_time_zone': None,
}


@singleton
class ProductTelemetry:
	"""
	Service for capturing anonymized telemetry data.

	If the environment variable `ANONYMIZED_TELEMETRY=False`, anonymized telemetry will be disabled.
	"""

	USER_ID_PATH = str(Path.home() / '.cache' / 'browser_use' / 'telemetry_user_id')
	PROJECT_API_KEY = 'phc_Xo4aVRcxXTKaV2mQSU0UbVRq5KwtM9xA9NAyjWqTUJo'
	HOST = 'https://us.i.posthog.com'
	UNKNOWN_USER_ID = 'UNKNOWN'

	_curr_user_id = None

	def __init__(self) -> None:
		telemetry_disabled = os.getenv('ANONYMIZED_TELEMETRY', 'true').lower() == 'false'
		self.debug_logging = os.getenv('BROWSER_USE_LOGGING_LEVEL', 'info').lower() == 'debug'

		if telemetry_disabled:
			self._posthog_client = None
		else:
			logging.info(
				'Telemetry is enabled.'
			)
			self._posthog_client = Posthog(
				project_api_key=self.PROJECT_API_KEY,
				host=self.HOST,
				disable_geoip=False,
			)

			# Silence posthog's logging
			if not self.debug_logging:
				posthog_logger = logging.getLogger('posthog')
				posthog_logger.disabled = True

		if self._posthog_client is None:
			logger.debug('Telemetry disabled')

	def capture(self, event: BaseTelemetryEvent) -> None:
		if self._posthog_client is None:
			return

		if self.debug_logging:
			logger.debug(f'Telemetry event: {event.name} {event.properties}')
		self._direct_capture(event)

	def _direct_capture(self, event: BaseTelemetryEvent) -> None:
		"""
		Should not be thread blocking because posthog magically handles it
		"""
		if self._posthog_client is None:
			return

		try:
			self._posthog_client.capture(
				self.user_id,
				event.name,
				{**event.properties, **POSTHOG_EVENT_SETTINGS},
			)
		except Exception as e:
			logger.error(f'Failed to send telemetry event {event.name}: {e}')

	@property
	def user_id(self) -> str:
		if self._curr_user_id:
			return self._curr_user_id

		# File access may fail due to permissions or other reasons. We don't want to
		# crash so we catch all exceptions.
		try:
			if not os.path.exists(self.USER_ID_PATH):
				os.makedirs(os.path.dirname(self.USER_ID_PATH), exist_ok=True)
				with open(self.USER_ID_PATH, 'w') as f:
					new_user_id = str(uuid.uuid4())
					f.write(new_user_id)
				self._curr_user_id = new_user_id
			else:
				with open(self.USER_ID_PATH, 'r') as f:
					self._curr_user_id = f.read()
		except Exception:
			self._curr_user_id = 'UNKNOWN_USER_ID'
		return self._curr_user_id
