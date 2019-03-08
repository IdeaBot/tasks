from libs import command
import re
import time

TIMES = {
            'second':1,
            'minute':60,
            'hour':60*60,
            'day':60*60*24, 'dai':60*60*24,
            'week':60*60*24*7
        }


class Command(command.DirectOnlyCommand):
    '''Create a reminder for later

**Usage**
```@Idea remind me to "<task>" in <time> [<repeat>] ```
Where
**`<task>`** is the description of the task you want to be reminded about
**`<time>`** is the time between now and the time you want to be reminded
**`<repeat>`** is the time period between reminders (optional)

**NOTE:** values for `<time>` must be positive whole numbers with a unit (days, hours, minutes, etc.)
**NOTE2:** [thing] means thing is optional

**Example**
`@Idea remind me to "do my homework" in 2 days and 3 hours`
`@Idea remind me to "Wake up" in 8 hours daily` '''

    def matches(self, message):
        return self.collect_args(message) is not None

    def collect_args(self, message):
        return re.search(r'remind\s*(me)\s*to\s+(.+)', message.content, re.I)

    def action(self, message):
        args = self.collect_args(message)
        args2 = self.finish_match(args.group(2))
        if args2 is None:
            yield from self.send_message(message.channel, 'Sorry, I lost you at `remind me to ...`. Use `@Idea help reminder` for usage instructions.')
            return
        time_to, repeat = get_times(args2.group(2))
        if time_to == -1:
            yield from self.send_message(message.channel, 'Unable to understand the time you gave. Use `@Idea help reminder` for usage instructions.')
            return

        if repeat == 0:
            yield from self.send_message(message.channel, 'It seems like you tried to specify a repetitive task, but I am unable to understand the `<repeat>` information.')
            return

        if repeat > 0:
            # create reminder with repeat value
            self.public_namespace.db.execute('INSERT INTO reminders (task, timestamp, owner, channel, repeat) VALUES (?,?,?,?,?)',\
                (args2.group(1), int(time_to+time.time()), message.author.id, message.channel.id, repeat))
            yield from self.send_message(message.channel, 'Successfully scheduled task to remind you in `%s` seconds every `%s` seconds' % (time_to, repeat) )
        else:
            # create reminder without repeat value
            self.public_namespace.db.execute('INSERT INTO reminders (task, timestamp, owner, channel) VALUES (?,?,?,?)',\
               (args2.group(1), int(time_to+time.time()), message.author.id, message.channel.id))
            yield from self.send_message(message.channel, 'Successfully scheduled task to remind you in `%s` seconds' % time_to)
        self.public_namespace.db.save()

    def finish_match(self, string):
        option1 = re.match(r'\"(.+)\"(?:\s*in\s*)?(.+)', string)
        option2 = re.match(r'(.+)\s+in\s*(.+)', string, re.I)
        # prefer match with quotes
        if option1 is not None:
            return option1
        return option2

def get_times(string):
    # two input options:
    # '<timestring> every <timestring> (...)' OR
    # '<timestring> <periodical>ly (...)'
    # I'm just making up words ^^^
    # check every case first
    args = re.search(r'\bevery\s+(\d+\s+.+)', string, re.I)
    if args is None:
        # case 2
        _time_to, end = timestring_to_seconds(string)
        _repeat = periodical_to_seconds(string[end:])
    else:
        # case 1
        _time_to, _ = timestring_to_seconds(string[:args.start()])
        _repeat, _ = timestring_to_seconds(args.group(1))
    return _time_to, _repeat


def timestring_to_seconds(string):
    time_accum = -1
    end = -1
    for match in re.finditer(r'(\d+)\s+(\w+)(?:\s+and)?', string):
        time_word = match.group(2).lower().rstrip('s')
        if time_word not in TIMES:
            return -1, end
        time_accum += TIMES[time_word]*int(match.group(1))
        end = match.end()
    if time_accum != -1:
        time_accum+=1  # correct for time_accum being set to -1 initially
    return time_accum, end

def periodical_to_seconds(string):
    match = re.match(r'\s*(\w+)ly\b', string)
    if match is not None and match.group(1).lower() in TIMES:
        return TIMES[match.group(1).lower()]
    else:
        return -1
