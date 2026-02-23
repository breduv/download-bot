from pydantic_settings import BaseSettings, SettingsConfigDict
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

class Settings(BaseSettings):
    
    BOT_TOKEN: str

    CLIENT_ID: str
    CLIENT_SECRET: str

    HTTPS_PROXY: str

    LOG_LEVEL: str

    @property
    def authorization(self):
        proxies = {
            "http": self.HTTPS_PROXY,
            "https": self.HTTPS_PROXY
        }

        return Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.CLIENT_ID,
                client_secret=self.CLIENT_SECRET),
            proxies=proxies
        )

    model_config = SettingsConfigDict()

settings = Settings()