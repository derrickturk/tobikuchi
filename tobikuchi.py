import re

class Script(object):
    def __init__(self):
        self.name = None
        self._display_name = None
        self.script = ''
        self.description = None
        self.inputs = []
        self.outputs = []
        self._describe_next = self

    @property
    def display_name(self):
        if self._display_name is None:
            return self.name
        else:
            return self._display_name

    @display_name.setter
    def display_name(self, name):
        self._display_name = name

    def add_script_line(self, line):
        self.script += line

    def add_description_line(self, line):
        if self.description is None:
            self.description = line.rstrip()
        else:
            self.description += '\n'
            self.description += line.rstrip()

    def add_input(self, input):
        if input.name in (i.name for i in self.inputs):
            raise ValueError('Duplicate input name.')
        self.inputs.append(input)
        self._describe_next = input

    def add_output(self, output):
        if output.name in (o.name for o in self.outputs):
            raise ValueError('Duplicate output name.')
        self.outputs.append(output)
        self._describe_next = output

    # add a description line to whatever is currently 'ready for description'
    #   i.e. first the script, then each input and output in turn, when doing
    #   a linear parse
    def describe_next(self, line):
        self._describe_next.add_description_line(line)

    def __str__(self):
        desc = 'Function %s (%s)\n%s' % (
            self.name,
            self.display_name,
            self.description + '\n' if self.description else ''
        )
        desc += 'Inputs:\n'
        for i in self.inputs:
            desc += '\t' + str(i) + '\n'
        desc += 'Outputs:\n'
        for o in self.outputs:
            desc += '\t' + str(o) + '\n'
        desc += 'Script:\n'
        desc += self.script
        return desc

class Input(object):
    def __init__(self):
        self.name = None
        self._display_name = None
        self.description = None
        self.category = None
        self.allowed_types = []
        self.optional = False

    @property
    def display_name(self):
        if self._display_name is None:
            return self.name
        else:
            return self._display_name

    @display_name.setter
    def display_name(self, name):
        self._display_name = name

    def add_description_line(self, line):
        if self.description is None:
            self.description = line.rstrip()
        else:
            self.description += '\n'
            self.description += line.rstrip()

    def __str__(self):
        return '%s { %s } :: %s%s of %s%s' % (
            self.name,
            self.display_name,
            'Optional ' if self.optional else '',
            self.category,
            ' | '.join(self.allowed_types),
            '\n\t' + self.description if self.description else ''
        )

class Output(object):
    def __init__(self):
        self.name = None
        self._display_name = None
        self.description = None
        self.category = None

    @property
    def display_name(self):
        if self._display_name is None:
            return self.name
        else:
            return self._display_name

    @display_name.setter
    def display_name(self, name):
        self._display_name = name

    def add_description_line(self, line):
        if self.description is None:
            self.description = line.rstrip()
        else:
            self.description += '\n'
            self.description += line.rstrip()

    def __str__(self):
        return '%s { %s } :: %s%s' % (
            self.name,
            self.display_name,
            self.category,
            '\n\t' + self.description if self.description else ''
        )

def parse(stream):
    script = Script()

    for line in stream:
        match = parse.annotation_re.match(line)
        if match:
            command = match.group(1).upper()
            if command not in handlers:
                raise ValueError('Invalid TK command.')
            handlers[command](script, line[match.span()[1]:].lstrip())
        script.add_script_line(line)

    return script
parse.annotation_re = re.compile(r'^\s*#\s*TK_(\w+)', re.I)

def parse_fn_name(script, line):
    script.name = line.rstrip()

def parse_fn_display_name(script, line):
    script.display_name = line.rstrip()

def parse_input(script, line):
    match = parse_input.input_re.match(line)
    if not match:
        raise ValueError('Invalid input description.')

    input = Input()
    input.name = match.group(1)

    if match.group(5) is not None:
        input.display_name = match.group(5).strip()

    if match.group(6) is not None:
        input.optional = True

    input.category = match.group(7)

    types = list(map(str.strip, match.group(8).split('|')))
    if any(t not in valid_types for t in types):
        raise ValueError('Invalid input type.')
    input.allowed_types = types

    script.add_input(input)
parse_input.input_re = re.compile(r'(((\.[_A-Za-z])|[A-Za-z])[._A-Za-z0-9]*)' +
        r'\s*({([^}]*)})?\s*::\s*(Optional)?\s*(Value|Column|Table)\s+of\s+' +
        r'(\w+(\s*\|\s*\w+)*)', re.I)

def parse_output(script, line):
    match = parse_output.output_re.match(line)
    if not match:
        raise ValueError('Invalid output description.')
    output = Output()
    output.name = match.group(1)
    if match.group(5) is not None:
        output.display_name = match.group(5).strip()
    output.category = match.group(6)
    script.add_output(output)
parse_output.output_re = re.compile(r'(((\.[_A-Za-z])|[A-Za-z])[._A-Za-z0-9]*)' +
        r'\s*({([^}]*)})?\s*::\s*(Value|Column|Table)', re.I)

def parse_description(script, line):
    script.describe_next(line)

handlers = {
    'FN': parse_fn_name,
    'DN': parse_fn_display_name,
    'IN': parse_input,
    'OUT': parse_output,
    'DESC': parse_description
}

valid_types = set([
    'Integer',
    'Real',
    'SingleReal',
    'Currency',
    'String',
    'Date',
    'Time',
    'DateTime',
    'Boolean',
    'Binary'
])

def main(argv):
    files = argv[1:]
    for fn in files:
        with open(fn) as f:
            script = parse(f)
            print(script)

import sys
if __name__ == '__main__':
    sys.exit(main(sys.argv))
