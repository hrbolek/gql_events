from typing import Optional, List, Union, Annotated
import strawberry
from dataclasses import dataclass
from contextlib import asynccontextmanager

from ._GraphResolvers import getLoadersFromInfo


###########################################################################################################################
#
# zde definujte sve GQL modely
# - nove, kde mate zodpovednost
# - rozsirene, ktere existuji nekde jinde a vy jim pridavate dalsi atributy
#
###########################################################################################################################
import datetime
from gql_events.GraphResolvers import resolveEventsForUser
from ._GraphResolvers import (
    IDType,

    resolve_reference,
    resolve_id,
    resolve_name,
    resolve_name_en,
    resolve_lastchange,
    resolve_created,
    resolve_createdby,
    resolve_changedby,

    asPage
    )

GroupGQLModel = Annotated["GroupGQLModel", strawberry.lazy(".GraphTypeDefinitionsExt")]
UserGQLModel = Annotated["UserGQLModel", strawberry.lazy(".GraphTypeDefinitionsExt")]

@strawberry.federation.type(keys=["id"], description="""Describes a relation of an user to the event by invitation (like invited) and participation (like absent)""")
class PresenceGQLModel:
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).presences

    resolve_reference = resolve_reference

    id = resolve_id
    lastchange = resolve_lastchange
    created = resolve_created
    createdby = resolve_createdby
    changedby = resolve_changedby

    @strawberry.field(description="""Present, Vacation etc.""")
    async def presence_type(self, info: strawberry.types.Info) -> Optional['PresenceTypeGQLModel']:
        result = await PresenceTypeGQLModel.resolve_reference(info, self.presencetype_id)
        return result

    @strawberry.field(description="""Invited, Accepted, etc.""")
    async def invitation_type(self, info: strawberry.types.Info) -> Optional['InvitationTypeGQLModel']:
        result = await InvitationTypeGQLModel.resolve_reference(info, self.invitation_id)
        return result

    @strawberry.field(description="""The user / participant""")
    async def user(self) -> Optional['UserGQLModel']:
        from .GraphTypeDefinitionsExt import UserGQLModel
        result = await UserGQLModel(id=self.user_id)
        return result

    @strawberry.field(description="""The event""")
    async def event(self, info: strawberry.types.Info) -> Optional['EventGQLModel']:
        result = await EventGQLModel.resolve_reference(info, id=self.event_id)
        return result

@strawberry.federation.type(keys=["id"], description="""Represents an event type""")
class EventTypeGQLModel:

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).eventtypes

    resolve_reference = resolve_reference

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en

    lastchange = resolve_lastchange
    created = resolve_created
    createdby = resolve_createdby
    changedby = resolve_changedby

    @strawberry.field(description="""Related events""")
    async def events(self, info: strawberry.types.Info) -> List['EventGQLModel']:
        loader = getLoadersFromInfo(info).event_eventtype_id
        result = await loader.load(self.id)
        return result

@strawberry.federation.type(keys=["id"], description="""Represents a type of presence (like Present)""")
class PresenceTypeGQLModel:

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).presencetypes

    resolve_reference = resolve_reference

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en

    lastchange = resolve_lastchange
    created = resolve_created
    createdby = resolve_createdby
    changedby = resolve_changedby


@strawberry.federation.type(keys=["id"], description="""Represents if an user has been invited to the event ot whatever""")
class InvitationTypeGQLModel:

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).presencetypes

    resolve_reference = resolve_reference

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en

    lastchange = resolve_lastchange
    created = resolve_created
    createdby = resolve_createdby
    changedby = resolve_changedby


from gql_events.GraphResolvers import resolveEventsForGroup


import datetime
from gql_events.GraphResolvers import (
    resolveEventById,
    resolveGroupsForEvent,
    resolvePresencesForEvent
)


@strawberry.federation.type(keys=["id"], description="""Entity representing an event (calendar item)""")
class EventGQLModel:

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).events

    resolve_reference = resolve_reference

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en

    lastchange = resolve_lastchange
    created = resolve_created
    createdby = resolve_createdby
    changedby = resolve_changedby

    @strawberry.field(description="""Date&time of event begin""")
    def startdate(self) -> Optional[datetime.datetime]:
        return self.startdate

    @strawberry.field(description="""Date&time of event end""")
    def enddate(self) -> Optional[datetime.datetime]:
        return self.enddate

    @strawberry.field(description="""Groups of users linked to the event""")
    async def groups(self, info: strawberry.types.Info) -> List["GroupGQLModel"]:
        from .GraphTypeDefinitionsExt import GroupGQLModel
        async with withInfo(info) as session:
            links = await resolveGroupsForEvent(session, self.id)
            # result = list(map(lambda item: GroupGQLModel(id=item.group_id), links))
            # return result
            return map(lambda item: GroupGQLModel(id=item.group_id), links)
            

    @strawberry.field(description="""Participants of the event and if they were absent or so...""")
    async def presences(self, info: strawberry.types.Info) -> List["PresenceGQLModel"]:
        loader = getLoadersFromInfo(info).presences
        result = await loader.filter_by(event_id=self.id)
        return result

    @strawberry.field(description="""Type of the event""")
    async def event_type(self, info: strawberry.types.Info) -> Optional["EventTypeGQLModel"]:
        result = await EventTypeGQLModel.resolve_reference(info=info, id=self.eventtype_id)
        return result

    @strawberry.field(description="""event which contains this event (aka semester of this lesson)""")
    async def master_event(self, info: strawberry.types.Info) -> Optional["EventGQLModel"]:
        result = None
        if (self.masterevent_id is not None):
            result = await EventGQLModel.resolve_reference(info=info, id=self.masterevent_id)
        return result

    @strawberry.field(description="""events which are contained by this event (aka all lessons for the semester)""")
    async def sub_events(self, info: strawberry.types.Info) -> List["EventGQLModel"]:
        loader = getLoadersFromInfo(info).events
        result = await loader.filter_by(masterevent_id=self.id)
        return result


###########################################################################################################################
#
# zde definujte resolvers pro Query model
#
###########################################################################################################################

from uoishelpers.resolvers import createInputs

@createInputs
@dataclass
class EventTypeInputFilter:
    name: str
    name_en: str

@strawberry.field(
    description="""Finds all types of events paged""",
    #permission_classes=[OnlyForAuthentized(isList=True)]
    )
@asPage
async def event_type_page(self, info: strawberry.types.Info, skip: Optional[int] = 0, limit: Optional[int] = 10, where: Optional[EventTypeInputFilter] = None) -> List["EventTypeGQLModel"]:
    return getLoadersFromInfo(info).eventtypes

@strawberry.field(
    description="""Gets type of event by id""",
    #permission_classes=[OnlyForAuthentized(isList=False)]
    )
async def event_type_by_id(self, info: strawberry.types.Info, id: IDType) -> Optional["EventTypeGQLModel"]:
    return await EventTypeGQLModel.resolve_reference(info=info, id=id)

@createInputs
@dataclass
class PresenceTypeInputFilter:
    name: str
    name_en: str

@strawberry.field(
    description="""Finds all types of presences paged""",
    #permission_classes=[OnlyForAuthentized(isList=True)]
    )
@asPage
async def presence_type_page(self, info: strawberry.types.Info, skip: Optional[int] = 0, limit: Optional[int] = 10, where: Optional[PresenceTypeInputFilter] = None) -> List["PresenceTypeGQLModel"]:
    return getLoadersFromInfo(info).presencetypes

@strawberry.field(
    description="""Gets type of presence by id""",
    #permission_classes=[OnlyForAuthentized(isList=False)]
    )
async def presence_type_by_id(self, info: strawberry.types.Info, id: IDType) -> Optional["PresenceTypeGQLModel"]:
    return await PresenceTypeGQLModel.resolve_reference(info=info, id=id)


@createInputs
@dataclass
class InvitationTypeInputFilter:
    name: str
    name_en: str

@strawberry.field(
    description="""Finds all types of invitation paged""",
    #permission_classes=[OnlyForAuthentized(isList=True)]
    )
@asPage
async def invitation_type_page(self, info: strawberry.types.Info, skip: Optional[int] = 0, limit: Optional[int] = 10, where: Optional[InvitationTypeInputFilter] = None) -> List["InvitationTypeGQLModel"]:
    return getLoadersFromInfo(info).invitationtypes

@strawberry.field(
    description="""Gets type of invitation by id""",
    #permission_classes=[OnlyForAuthentized(isList=False)]
    )
async def invitation_type_by_id(self, info: strawberry.types.Info, id: IDType) -> Optional["InvitationTypeGQLModel"]:
    return await InvitationTypeGQLModel.resolve_reference(info=info, id=id)


@createInputs
@dataclass
class EventInputFilter:
    name: str
    name_en: str
    startdate: datetime.datetime
    enddate: datetime.datetime
    type_id: IDType

@strawberry.field(
    description="""Finds all events paged""",
    #permission_classes=[OnlyForAuthentized(isList=True)]
    )
@asPage
async def event_page(self, info: strawberry.types.Info, skip: Optional[int] = 0, limit: Optional[int] = 10, where: Optional[EventInputFilter] = None) -> List["EventGQLModel"]:
    return getLoadersFromInfo(info).events

@strawberry.field(
    description="""Gets event by id""",
    #permission_classes=[OnlyForAuthentized(isList=False)]
    )
async def event_by_id(self, info: strawberry.types.Info, id: IDType) -> Optional["EventGQLModel"]:
    return await EventGQLModel.resolve_reference(info=info, id=id)

@createInputs
@dataclass
class PresenceInputFilter:
    name: str
    name_en: str

@asPage
async def presence_page(self, info: strawberry.types.Info, skip: Optional[int] = 0, limit: Optional[int] = 10, where: Optional[PresenceInputFilter] = None) -> List["PresenceGQLModel"]:
    return getLoadersFromInfo(info).events

async def presence_by_id(self, info: strawberry.types.Info, id: IDType) -> Optional["PresenceGQLModel"]:
    return await PresenceGQLModel.resolve_reference(info=info, id=id)


###########################################################################################################################
#
# zde definujte svuj Query model
#
###########################################################################################################################

@strawberry.type(description="""Type for query root""")
class Query:
    event_by_id = event_by_id
    event_page = event_page

    event_type_by_id = event_type_by_id
    event_type_page = event_type_page

    presence_type_by_id = presence_type_by_id
    presence_type_page = presence_type_page

    invitation_type_by_id = invitation_type_by_id
    invitation_type_page = invitation_type_page

###########################################################################################################################
#
# zde definujte resolvers pro Mutation model
#
###########################################################################################################################

from typing import Optional

@strawberry.input(description="Datastructure for insert")
class EventInsertGQLModel:
    name: str
    eventtype_id: IDType
    id: Optional[IDType] = None
    masterevent_id: Optional[IDType] = None
    startdate: Optional[datetime.datetime] = \
        strawberry.field(description="start date of event", default_factory=lambda: datetime.datetime.now())
    enddate: Optional[datetime.datetime] = \
        strawberry.field(description="end date of event", default_factory=lambda:datetime.datetime.now() + datetime.timedelta(minutes = 30))    
    pass

@strawberry.input(description="Datastructure for update")
class EventUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    name: Optional[str] = None
    masterevent_id: Optional[IDType] = None
    eventtype_id: Optional[IDType] = None
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None
    
@strawberry.type(description="""Result of user operation""")
class EventResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of user operation""")
    async def event(self, info: strawberry.types.Info) -> Union[EventGQLModel, None]:
        result = await EventGQLModel.resolve_reference(info, self.id)
        return result

from ._GraphResolvers import (
    encapsulateInsert,
    encapsulateUpdate
)

# @strawberry.mutation(description="creates new event")
# async def event_insert(self, info: strawberry.types.Info, event: EventInsertGQLModel) -> EventResultGQLModel:
#     return EventResultGQLModel()
#     # return await encapsulateInsert(getLoadersFromInfo(info).events, event, EventResultGQLModel(id=None, msg="ok"))

@strawberry.mutation(
    description="C operation",
        # permission_classes=[OnlyForAuthentized()]
        )
async def event_insert(self, info: strawberry.types.Info, event: EventInsertGQLModel) -> EventResultGQLModel:
    # user = getUserFromInfo(info)
    # event.createdby = IDType(user["id"])

    loader = getLoadersFromInfo(info).events
    row = await loader.insert(event)
    result = EventResultGQLModel(id=row.id, msg="ok")
    return result


@strawberry.mutation(description="updates the event")
async def event_update(self, info: strawberry.types.Info, event: EventUpdateGQLModel) -> EventResultGQLModel:
    return await encapsulateUpdate(getLoadersFromInfo(info).events, event, EventResultGQLModel(id=None, msg="ok"))


@strawberry.input(description="Datastructure for insert")
class PresenceInsertGQLModel:
    user_id: IDType
    event_id: IDType
    invitation_id: IDType
    presencetype_id: Optional[IDType] = None
    id: Optional[IDType] = None

@strawberry.input(description="Datastructure for update")
class PresenceUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    invitation_id: Optional[IDType] = None
    presencetype_id: Optional[IDType] = None
    
@strawberry.type(description="""Result of user operation""")
class PresenceResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of presence operation""")
    async def presence(self, info: strawberry.types.Info) -> Union[PresenceGQLModel, None]:
        result = await PresenceGQLModel.resolve_reference(info, self.id)
        return result

@strawberry.mutation(description="creates new presence")
async def presence_insert(self, info: strawberry.types.Info, presence: PresenceInsertGQLModel) -> PresenceResultGQLModel:
    return await encapsulateInsert(getLoadersFromInfo(info).presences, presence, PresenceResultGQLModel(id=None, msg="ok"))

@strawberry.mutation(description="updates the event")
async def presence_update(self, info: strawberry.types.Info, presence: PresenceUpdateGQLModel) -> PresenceResultGQLModel:
    return await encapsulateUpdate(getLoadersFromInfo(info).presences, presence, PresenceResultGQLModel(id=None, msg="ok"))


@strawberry.input(description="First datastructure for event type creation")
class EventTypeInsertGQLModel:
    name: str = strawberry.field(description="name of event type")
    name_en: str
    id: Optional[IDType] = None

@strawberry.input(description="Datastructure for event type update")
class EventTypeUpdateGQLModel:
    id: IDType
    name: Optional[str] = None
    name_en: Optional[str] = None

@strawberry.type(description="""Result of event type operation""")
class EventTypeResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Event type""")
    async def event_type(self, info: strawberry.types.Info) -> Optional[EventTypeGQLModel]:
        result = await EventTypeGQLModel.resolve_reference(info, self.id)
        return result
    
@strawberry.mutation(description="creates new presence")
async def event_type_insert(self, info: strawberry.types.Info, event_type: EventTypeInsertGQLModel) -> EventTypeResultGQLModel:
    return await encapsulateInsert(getLoadersFromInfo(info).presences, event_type, EventTypeResultGQLModel(id=None, msg="ok"))

@strawberry.mutation(description="updates the event")
async def event_type_update(self, info: strawberry.types.Info, event_type: EventTypeUpdateGQLModel) -> EventTypeResultGQLModel:
    return await encapsulateUpdate(getLoadersFromInfo(info).presences, event_type, EventTypeResultGQLModel(id=None, msg="ok"))


@strawberry.input(description="First datastructure for event type creation")
class PresenceTypeInsertGQLModel:
    name: str
    name_en: str
    id: Optional[IDType] = None

@strawberry.input(description="Datastructure for event type update")
class PresenceTypeUpdateGQLModel:
    id: IDType
    name: Optional[str] = None
    name_en: Optional[str] = None

@strawberry.type(description="""Result of event type operation""")
class PresenceTypeResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Presence type""")
    async def presence_type(self, info: strawberry.types.Info) -> Optional[PresenceTypeGQLModel]:
        result = await PresenceTypeGQLModel.resolve_reference(info, self.id)
        return result
    
@strawberry.mutation(description="creates new presence type")
async def presence_type_insert(self, info: strawberry.types.Info, presence_type: PresenceTypeInsertGQLModel) -> PresenceTypeResultGQLModel:
    return await encapsulateInsert(getLoadersFromInfo(info).presencetypes, presence_type, EventTypeResultGQLModel(id=None, msg="ok"))

@strawberry.mutation(description="updates the event")
async def presence_type_update(self, info: strawberry.types.Info, presence_type: PresenceTypeUpdateGQLModel) -> PresenceTypeResultGQLModel:
    return await encapsulateUpdate(getLoadersFromInfo(info).presencetypes, presence_type, PresenceTypeResultGQLModel(id=None, msg="ok"))

@strawberry.input(description="First datastructure for invitation type creation")
class InvitationTypeInsertGQLModel:
    name: str
    name_en: str
    id: Optional[IDType] = None

@strawberry.input(description="Datastructure for invitation type update")
class InvitationTypeUpdateGQLModel:
    id: IDType
    name: Optional[str] = None
    name_en: Optional[str] = None

@strawberry.type(description="""Result of event type operation""")
class InvitationTypeResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Presence type""")
    async def invitation_type(self, info: strawberry.types.Info) -> Optional[InvitationTypeGQLModel]:
        result = await PresenceTypeGQLModel.resolve_reference(info, self.id)
        return result
    
@strawberry.mutation(description="creates new presence type")
async def invitation_type_insert(self, info: strawberry.types.Info, invitation_type: InvitationTypeInsertGQLModel) -> InvitationTypeResultGQLModel:
    return await encapsulateInsert(getLoadersFromInfo(info).presencetypes, invitation_type, InvitationTypeResultGQLModel(id=None, msg="ok"))

@strawberry.mutation(description="updates the event")
async def invitation_type_update(self, info: strawberry.types.Info, invitation_type: InvitationTypeUpdateGQLModel) -> InvitationTypeResultGQLModel:
    return await encapsulateUpdate(getLoadersFromInfo(info).presencetypes, invitation_type, InvitationTypeResultGQLModel(id=None, msg="ok"))


###########################################################################################################################
#
# zde definujte Mutation model
#
###########################################################################################################################


@strawberry.federation.type(extend=True)
class Mutation:
    event_insert = event_insert
    event_update = event_update

    presence_insert = presence_insert
    presence_update = presence_update

    event_type_insert = event_type_insert
    event_type_update = event_type_update

    presence_type_insert = presence_type_insert
    presence_type_update = presence_type_update

    invitation_type_insert = invitation_type_insert
    invitation_type_update = invitation_type_update
    # pass

    
###########################################################################################################################
#
# Schema je pouzito v main.py, vsimnete si parametru types, obsahuje vyjmenovane modely. Bez explicitniho vyjmenovani
# se ve schema objevi jen ty struktury, ktere si strawberry dokaze odvodit z Query. Protoze v teto konkretni implementaci
# nektere modely nejsou s Query propojene je potreba je explicitne vyjmenovat. Jinak ve federativnim schematu nebude
# dostupne rozsireni, ktere tento prvek federace implementuje.
#
###########################################################################################################################

from .GraphTypeDefinitionsExt import UserGQLModel
schema = strawberry.federation.Schema(Query, types=(UserGQLModel,), mutation=Mutation)
#schema = strawberry.federation.Schema(Query, types=(UserGQLModel,))
