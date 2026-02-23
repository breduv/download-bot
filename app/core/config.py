from pydantic_settings import BaseSettings, SettingsConfigDict
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

class Settings(BaseSettings):
    
    BOT_TOKEN: str

    CLIENT_ID: str
    CLIENT_SECRET: str

    PROXY: str
    PROXY2: str

    LOG_LEVEL: str

    @property
    def authorization(self):
        proxies = {
            "http": self.PROXY,
            "https": self.PROXY
        }

        return Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.CLIENT_ID,
                client_secret=self.CLIENT_SECRET),
            proxies=proxies
        )

    model_config = SettingsConfigDict()

settings = Settings()