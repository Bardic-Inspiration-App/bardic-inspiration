import logging 
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from spotipy.oauth2 import SpotifyOAuth, SpotifyStateError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Server Browser
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run Chrome in headless mode
webdriver_path = '/app/.chromedriver/bin/chromedriver' if os.getenv('DEVELOPMENT_MODE', False) else '/path/to/chromedriver' #fixme


class CustomSpotifyOAuth(SpotifyOAuth):
    """ 
    Custom wrapper to allow the bot to authenticate itself.
    User Landon Turner has given permission with use of Bardic Inspiration
    """

    # def _get_auth_response_interactive(self, open_browser=False):
    #     if open_browser:
    #         raise Exception("Custom class was intenrally misconfigured")
    #     else:
    #         url = self.get_authorize_url()
    #     state, code = SpotifyOAuth.parse_auth_response_url(url)
    #     if self.state is not None and self.state != state:
    #         raise SpotifyStateError(self.state, state)
    #     return code
    
    def _open_auth_url(self):
        auth_url = self.get_authorize_url()
        try:
            driver = webdriver.Chrome(executable_path=webdriver_path, options=chrome_options)
            driver.get(auth_url)

            driver.quit()
        except Exception as e:
            logger.error(f"Failed to auth: {auth_url}. {e}" )