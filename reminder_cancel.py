from libs import command
import re

class Command(command.DirectOnlyCommand):
    '''Cancel a reminder

**Usage**
```@Idea cancel next reminder```

```@Idea cancel all reminders``` '''

    def matches(self, message):
        return self.collect_args(message) is not None

    def collect_args(self, message):
        return re.search(r'cancel\s+(\w+)\s+(?:(\d+)\s+)?reminders?', message.content, re.I)

    def action(self, message):
        args = self.collect_args(message)
        if args.group(2) is not None:
            repetitions = int(args.group(2))
        else:
            repetitions = 1

        successes = 0
        if args.group(1).lower() == 'all':
            self.public_namespace.db.execute('UPDATE reminders SET complete=1 WHERE owner=? and complete=0', (message.author.id,))
            repetitions = 0
            successes = 'all'
        elif args.group(1).lower() == 'next':
            self.public_namespace.db.execute('SELECT id FROM reminders WHERE owner=? and complete=0 ORDER BY timestamp ASC', (message.author.id,))
        rows = self.public_namespace.db.cursor.fetchall()
        for i in range(repetitions):
            if i<len(rows):
                self.public_namespace.db.execute('UPDATE reminders SET complete=1 WHERE id=?', (rows[i]['id'], ))
                successes += 1
        yield from self.send_message(message.channel, 'Canceled %s reminder(s)' % successes)
        self.public_namespace.db.save()
