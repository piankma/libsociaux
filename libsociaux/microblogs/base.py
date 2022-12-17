import dataclasses
import typing


class MicroBlogPosts:
    def __init__(self, service: "MicroBlog"):
        self.service = service


@dataclasses.dataclass
class Post:
    ...


class MicroBlogComments(MicroBlogPosts):
    ...


@dataclasses.dataclass
class Comment(Post):
    ...


class MicroBlogDMs:
    def __init__(self, service: "MicroBlog"):
        self.service = service


@dataclasses.dataclass
class DM:
    ...


class MicroBlogUsers:
    def __init__(self, service: "MicroBlog"):
        self.service = service


@dataclasses.dataclass
class User:
    _service: "MicroBlog"
    id: str
    full_name: str
    username: str
    description: str = None
    location: str = None
    url: str = None
    is_private: bool = False

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.username} ({self.full_name})>"


class MicroBlog:
    ID: str = None
    NAME: str = None
    URL: str = None

    def __init__(self, config: dict[str, typing.Any]):
        self.config = config

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.users.current_user.username}>"

    @property
    def users(self) -> MicroBlogUsers:
        """Subclass for handling interactions with users"""
        raise NotImplementedError

    @property
    def dms(self) -> MicroBlogDMs:
        raise NotImplementedError

    @property
    def posts(self) -> MicroBlogPosts:
        raise NotImplementedError

    @property
    def comments(self) -> MicroBlogComments:
        raise NotImplementedError
