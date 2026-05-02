"""v50b ORM model snapshot — importing all classes here registers them
against the snapshot's isolated Base.metadata.
"""

from .user import User, UserRole  # noqa: F401
from .event import Event, EventStatus  # noqa: F401
from .participant import Participant, RegistrationStatus  # noqa: F401
from .event_field_config import EventFieldConfig  # noqa: F401
from .custom_field import CustomFieldDefinition, CustomFieldValue  # noqa: F401
from .note import Note  # noqa: F401
from .allocation_category import AllocationCategory  # noqa: F401
from .allocation_unit import AllocationUnit  # noqa: F401
from .allocation import Allocation  # noqa: F401
from .user_preferences import UserPreferences  # noqa: F401
from .checkin_field import CheckInField  # noqa: F401
from .checkin_value import CheckInValue  # noqa: F401
from .mark import MarkDefinition, MarkAssignment  # noqa: F401
from .event_assignment import StaffGroup, EventUserAssignment  # noqa: F401
from .preference_request import ParticipantPreferenceRequest  # noqa: F401
