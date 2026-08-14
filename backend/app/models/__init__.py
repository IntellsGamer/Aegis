"""ORM models package. Importing this package registers all tables."""
from app.models.user import *  # noqa: F401,F403
from app.models.scan import *  # noqa: F401,F403
from app.models.threat import *  # noqa: F401,F403
from app.models.keyword import *  # noqa: F401,F403
from app.models.rule import *  # noqa: F401,F403
from app.models.learning import *  # noqa: F401,F403
from app.models.log import *  # noqa: F401,F403
from app.models.notification import *  # noqa: F401,F403
