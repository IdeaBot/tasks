from libs import plugin, dataloader
import time
import discord

COLUMNS_TO_PATCH = {}

CREATE_TABLE_SQL = ''' CREATE TABLE IF NOT EXISTS reminders
(
id INTEGER PRIMARY KEY,
task TEXT NOT NULL,
timestamp INTEGER NOT NULL,
owner TEXT NOT NULL,
channel TEXT NOT NULL,
repeat INTEGER,
complete INTEGER NOT NULL DEFAULT 0
) '''


class Plugin(plugin.ThreadedPlugin, plugin.OnReadyPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, should_spawn_thread=False, **kwargs)

        self.public_namespace.database = self.public_namespace.db = dataloader.datafile(self.config['database'])
        # create table if not exists
        self.public_namespace.db.execute(CREATE_TABLE_SQL)
        # create new columns if not exist
        self.public_namespace.db.patch('reminders', COLUMNS_TO_PATCH, commit=True)
        self.this_run = 0
        self.spawn_process()

    def threaded_action(self, q):
        self.this_run, self.last_run = int(time.time()), self.this_run
        self.public_namespace.db.execute('SELECT * FROM reminders WHERE timestamp < ? and complete = 0', (self.last_run, ))
        for row in self.public_namespace.db.cursor.fetchall():
            payload = dict()
            message_args = dict()
            content = ('<@!%s>' % row['owner']) + ' **__REMINDER__**\n' + row['task']
            message_args[plugin.ARGS] = [discord.Object(id=row['channel']), content]
            payload[self.SEND_MESSAGE] = message_args
            q.put(payload)
            # do completing updates
            if row['repeat'] is not None:
                print(row['repeat'])
                new_timestamp = row['timestamp'] + row['repeat']
                self.public_namespace.db.execute('UPDATE reminders SET timestamp=? WHERE id=?', (new_timestamp, row['id']))
            else:
                self.public_namespace.db.execute('UPDATE reminders SET complete=1 WHERE id=?', (row['id'], ))
        self.public_namespace.db.save()
