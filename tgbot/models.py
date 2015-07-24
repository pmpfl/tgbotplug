from peewee import (
    Proxy, Model, CharField, IntegerField,
    ForeignKeyField, DateTimeField, BooleanField,
)
import datetime


database_proxy = Proxy()


class BotModel(Model):
    class Meta:
        database = database_proxy


class GroupChat(BotModel):
    id = IntegerField(primary_key=True)
    title = CharField()


class User(BotModel):
    id = IntegerField(primary_key=True)
    first_name = CharField()
    last_name = CharField()


class Message(BotModel):
    id = IntegerField(primary_key=True)
    # group_chat can be None if it's a user chat (only sender is used)
    group_chat = ForeignKeyField(GroupChat, null=True, index=True)
    sender = ForeignKeyField(User, index=True)
    text = CharField()
    reply_id = IntegerField(null=True, index=True)
    date = DateTimeField(default=datetime.datetime.now)
    reply_plugin = CharField(index=True)
    reply_method = CharField()
    reply_selective = BooleanField(default=True)


class PluginData(BotModel):
    name = CharField()
    k1 = CharField()
    k2 = CharField(null=True)
    data = CharField(null=True)

    class Meta:
        indexes = (
            (('name', 'k1'), False),
        )


def create_tables(db):
    db.create_tables([GroupChat, User, Message, PluginData])
