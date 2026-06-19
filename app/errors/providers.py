class ProviderError(Exception):
    pass


class SpotifyProviderError(ProviderError):
    pass


class YtdlpProviderError(ProviderError):
    pass


class ThumbnailProviderError(ProviderError):
    pass


class AudioMetadataProviderError(ProviderError):
    pass


class MediaNotFoundError(ProviderError):
    pass