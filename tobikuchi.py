import re

class Script(object):
    def __init__(self):
        self.name = None
        self._display_name = None
        self.script = ''
        self.description = None
        self.inputs = []
        self.outputs = []

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

    def add_output(self, output):
        if output.name in (o.name for o in self.outputs):
            raise ValueError('Duplicate output name.')
        self.output.append(output)

class Input(object):
    def __init__(self):
        self.name = None
        self._display_name = None
        self.description = None
        self.category = None
        self.allowed_types = []

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
    input.category = match.group(6)
    types = map(str.strip, match.group(7).split('|'))
    if any(t not in valid_types for t in types):
        raise ValueError('Invalid input type.')
    script.add_input(input)
parse_input.input_re = re.compile(r'(((\.[_A-Za-z])|[A-Za-z])[._A-Za-z0-9]*)' +
        r'\s*({([^}]*)})?\s*::\s*(Value|Column|Table)\s+of\s+' +
        r'(\w+(\s*\|\s*\w+)*)', re.I)

def parse_output(script, line):
    pass

def parse_description(script, line):
    script.add_description_line(line)

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
            print(script.name)
            print(script.script)
            for i in script.inputs:
                print(i.name)

import sys
if __name__ == '__main__':
    sys.exit(main(sys.argv))
