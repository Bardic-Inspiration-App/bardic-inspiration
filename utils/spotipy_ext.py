import logging 
import os
from six.moves.urllib_parse import parse_qsl, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from spotipy.oauth2 import SpotifyOAuth, SpotifyStateError, SpotifyOauthError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Server Browser
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run Chrome in headless mode
webdriver_path = '/app/.apt/usr/bin/google-chrome instead.' if os.getenv('DEVELOPMENT_MODE', False) else '/usr/local/chromedriver/' #fixme
chrome_service = Service(executable_path=webdriver_path)


class CustomSpotifyOAuth(SpotifyOAuth):
    """ 
    Custom wrapper to allow the bot to authenticate itself.
    User Landon Turner has given permission with use of Bardic Inspiration
    """
    @staticmethod
    def parse_auth_response_url(url):
        logging.info(f'AUTH URL: {url}')
        query_s = urlparse(url).query
        logging.info(f'QUERY_S: {query_s}')
        form = dict(parse_qsl(query_s))
        # {'client_id': 'accurate', 'response_type': 'code', 'redirect_uri': "'http://localhost:8888/callback'", 'scope': 'user-library-read playlist-read-private user-modify-playback-state'}
        logging.info(f'FORM: {form}')
        logging.info(f'FORM GET: {[form.get(param) for param in ["state", "code"]]}')
        logging.info(f'TUPLE: {tuple(form.get(param) for param in ["state", "code"])}')
        if "error" in form:
            raise SpotifyOauthError("Received error from auth server: "
                                    "{}".format(form["error"]),
                                    error=form["error"])
        return tuple(form.get(param) for param in ["state", "code"])

    def _get_auth_response_interactive(self, open_browser=False):
        if open_browser:
            raise Exception("Custom class was intenrally misconfigured")
        else:
            url = self.get_authorize_url()
        state, code = self.parse_auth_response_url(url)
        logger.info(f"STATE: {state}, CODE: {code}")
        if self.state is not None and self.state != state:
            raise SpotifyStateError(self.state, state)
        return code
    
    def _open_auth_url(self):
        auth_url = self.get_authorize_url()
        try:
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            driver.get(auth_url)
        except Exception as e:
            logger.error(f"Failed to auth: {auth_url}. {e}" )
            driver.quit()