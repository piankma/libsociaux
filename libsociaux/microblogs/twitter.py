import dataclasses
from datetime import datetime
from cachetools.func import ttl_cache
import tweepy

from libsociaux.core import exceptions as err
from libsociaux.microblogs import base

PAGINATION_COUNT = 200
TTL_CACHE_TIME = 900


def twitter_exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tweepy.errors.Unauthorized as e_unauth:
            raise err.InvalidCredentials('\n'.join(e_unauth.api_messages)) from e_unauth
        except tweepy.errors.TooManyRequests as e_tmr:
            raise err.QuotaExceeded('\n'.join(e_tmr.api_messages)) from e_tmr
        except tweepy.errors.NotFound as e_nf:
            raise err.NotFound('\n'.join(e_nf.api_messages)) from e_nf
        except tweepy.errors.HTTPException as e:
            raise err.ServiceError('\n'.join(e.api_messages)) from e

    return wrapper


class TwitterUser(base.User):
    def __repr__(self):
        return f"<{self.__class__.__name__} @{self.username} - {self.full_name}>"

    @staticmethod
    def from_tweepy_user(service: "Twitter", tweepy_user: tweepy.User) -> "TwitterUser":
        """
        Maps a tweepy.User object to a libsociaux User object.

        :param service: The service that the user belongs to.
        :param tweepy_user: The tweepy.User object to map.
        :return: A libsociaux User object."""
        return TwitterUser(
            _service=service,
            id=tweepy_user.id_str or str(tweepy_user.id),
            full_name=tweepy_user.name,
            username=tweepy_user.screen_name,
            description=tweepy_user.description,
            location=tweepy_user.location,
            url=tweepy_user.url,
            is_private=tweepy_user.protected,
        )


class TwitterUsers(base.MicroBlogUsers):
    @twitter_exception_handler
    @property
    def current_user(self) -> TwitterUser:
        """
        Returns the current user profile.
        :returns: Current user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.verify_credentials())

    @twitter_exception_handler
    @ttl_cache(ttl=900)
    def get_user(self, username: str | None = None, user_id: str | int | None = None) -> TwitterUser:
        """
        Returns user profile by the username. Cached for TTL_CACHE_TIME minutes.
        :param username: User's screen name
        :param user_id: User's ID
        :returns: User profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        if username:
            return TwitterUser.from_tweepy_user(self.service, self.service.api.get_user(screen_name=username))
        elif user_id:
            return TwitterUser.from_tweepy_user(self.service, self.service.api.get_user(user_id=user_id))
        else:
            raise ValueError("Either username or user_id must be provided.")

    @twitter_exception_handler
    def follow(self, username: str) -> TwitterUser:
        """
        Follows the user.
        :param username: User's screen name
        :return: Followed user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.create_friendship(screen_name=username))

    @twitter_exception_handler
    def unfollow(self, username: str) -> TwitterUser:
        """
        Unfollows the user.
        :param username: User's screen name to unfollow.
        :return: Unfollowed user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.destroy_friendship(screen_name=username))

    @twitter_exception_handler
    def block(self, username: str) -> TwitterUser:
        """
        Blocks the user.
        :param username: User's screen name to block.
        :return: Blocked user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.create_block(screen_name=username))

    @twitter_exception_handler
    def unblock(self, username: str) -> TwitterUser:
        """
        Unblocks the user.
        :param username: User's screen name to unblock.
        :return: Unblocked user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.destroy_block(screen_name=username))

    @twitter_exception_handler
    def mute(self, username: str) -> TwitterUser:
        """
        Mutes the user.
        :param username: User's screen name to mute.
        :return: Muted user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.create_mute(screen_name=username))

    @twitter_exception_handler
    def unmute(self, username: str) -> TwitterUser:
        """
        Unmutes the user.
        :param username: User's screen name to unmute.
        :return: Unmuted user profile.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return TwitterUser.from_tweepy_user(self.service, self.service.api.destroy_mute(screen_name=username))

    @twitter_exception_handler
    @ttl_cache(ttl=TTL_CACHE_TIME)
    def list_followers(self, username: str | None = None) -> list[TwitterUser]:
        """
        Returns the list of followers for the given user. Cached for TTL_CACHE_TIME minutes.
        :param username: User's screen name to get followers from. If None, the current user is used.
        :return: List of followers.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        if not username:
            username = self.current_user.username

        return [
            TwitterUser.from_tweepy_user(self.service, user)
            for user in
            tweepy.Cursor(self.service.api.get_followers, count=PAGINATION_COUNT, screen_name=username).items()
        ]

    @twitter_exception_handler
    @ttl_cache(ttl=TTL_CACHE_TIME)
    def list_following(self, username: str | None = None) -> list[TwitterUser]:
        """
        Returns the list of users followed by the given user. Cached for TTL_CACHE_TIME minutes.
        :param username: User's screen name to get following from. If None, the current user is used.
        :return: List of users followed by the given user.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        if not username:
            username = self.current_user.username

        return [
            TwitterUser.from_tweepy_user(self.service, user)
            for user in
            tweepy.Cursor(self.service.api.get_friends, count=PAGINATION_COUNT, screen_name=username).items()
        ]

    @twitter_exception_handler
    @ttl_cache(ttl=TTL_CACHE_TIME)
    def list_blocked(self) -> list[TwitterUser]:
        """
        Returns the list of blocked users. Cached for TTL_CACHE_TIME minutes.
        :return: List of blocked users.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises ServiceError: If the service returns an unknown error.
        """
        return [
            TwitterUser.from_tweepy_user(self.service, user)
            for user in tweepy.Cursor(self.service.api.get_blocks).items()
        ]

    @twitter_exception_handler
    @ttl_cache(ttl=TTL_CACHE_TIME)
    def list_muted(self) -> list[TwitterUser]:
        """
        Returns the list of muted users. Cached for TTL_CACHE_TIME minutes.
        :return: List of muted users.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises ServiceError: If the service returns an unknown error.
        """
        return [
            TwitterUser.from_tweepy_user(self.service, user)
            for user in tweepy.Cursor(self.service.api.get_mutes).items()
        ]


@dataclasses.dataclass
class TwitterDM(base.DM):
    id: str
    sender: TwitterUser
    recipients: [TwitterUser]
    text: str
    created_at: datetime
    is_read: bool | None

    def __repr__(self):
        return f"<TwitterDM @{self.sender.username} to @{', @'.join([i.username for i in self.recipients])}>"

    @staticmethod
    def from_tweepy_dm(service: base.MicroBlog, dm: tweepy.DirectMessageEvent) -> "TwitterDM":
        return TwitterDM(
            id=dm.id,
            sender=service.users.get_user(user_id=int(dm.message_create['sender_id'])),
            recipients=[service.users.get_user(user_id=int(dm.message_create['target']['recipient_id']))],
            text=dm.message_create['message_data']['text'],
            created_at=datetime.fromtimestamp(int(dm.created_timestamp) / 1000000000),
            is_read=None,
        )


class TwitterDMs(base.MicroBlogDMs):
    def get(self, dm_id: str) -> TwitterDM:
        """
        Returns the DM with the given ID.
        :param dm_id: Direct message ID.
        :return: Direct message.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the DM is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        # return TwitterDM.from_tweepy_dm(self.service, self.service.api.get_direct_message(dm_id))
        ...

    def list_threads(self, username: str | None = None) -> list[TwitterDM]:
        """
        Returns the list of DMs.
        :param username: User's screen name to get DMs from. If None, the current user is used.
        :return: List of DMs.
        :raises QuotaExceeded: If the quota is exceeded.
        :raises NotFound: If the user is not found.
        :raises ServiceError: If the service returns an unknown error.
        """
        return [
            TwitterDM.from_tweepy_dm(self.service, dm)
            for dm in
            tweepy.Cursor(self.service.api.get_direct_messages, count=PAGINATION_COUNT).items()
        ]


class Twitter(base.MicroBlog):
    ID = "twitter"
    NAME = "Twitter"
    URL = "https://twitter.com"

    def __init__(self, config: dict):
        super().__init__(config)

        self.config = config
        for key in ("consumer_key", "consumer_secret", "access_token", "access_token_secret"):
            if key not in config.keys():
                raise ValueError(f"Missing {key} in Twitter config")

    @property
    def api(self) -> tweepy.API:
        """
        Creates a new tweepy.API object.
        :return: A new API object to call the Twitter API.
        :raises InvalidCredentials: If the credentials are invalid.
        :raises ServiceError: If the service returns an unknown error.
        """
        auth = tweepy.OAuth1UserHandler(
            self.config["consumer_key"],
            self.config["consumer_secret"],
            self.config["access_token"],
            self.config["access_token_secret"],
        )

        return tweepy.API(auth, wait_on_rate_limit=True)

    @property
    def users(self) -> TwitterUsers:
        return TwitterUsers(service=self)

    @property
    def dms(self) -> TwitterDMs:
        return TwitterDMs(service=self)
