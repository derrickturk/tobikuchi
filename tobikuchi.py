import re

from Spotfire.Dxp.Data.DataFunctions import *
from Spotfire.Dxp.Data import DataType

class Script(object):
    def __init__(self):
        self.name = None
        self._display_name = None
        self.script = ''
        self.description = None
        self.inputs = []
        self.outputs = []
        self._describe_next = self

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

    def _get_display_name(self):
        if self._display_name is None:
            return self.name
        else:
            return self._display_name

    def _set_display_name(self, name):
        self._display_name = name

    display_name = property(_get_display_name, _set_display_name)

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

    def add_description_line(self, line):
        if self.description is None:
            self.description = line.rstrip()
        else:
            self.description += '\n'
            self.description += line.rstrip()

    def _get_display_name(self):
        if self._display_name is None:
            return self.name
        else:
            return self._display_name

    def _set_display_name(self, name):
        self._display_name = name

    display_name = property(_get_display_name, _set_display_name)

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

    def add_description_line(self, line):
        if self.description is None:
            self.description = line.rstrip()
        else:
            self.description += '\n'
            self.description += line.rstrip()

    def _get_display_name(self):
        if self._display_name is None:
            return self.name
        else:
            return self._display_name

    def _set_display_name(self, name):
        self._display_name = name

    display_name = property(_get_display_name, _set_display_name)


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

    input.category = canonize(match.group(7))

    types = list(map(lambda s: canonize(s.strip()), match.group(8).split('|')))
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
    output.category = canonize(match.group(6))
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

canonical = {
    'INTEGER': ('Integer', DataType.Integer),
    'REAL': ('Real', DataType.Real),
    'SINGLEREAL': ('SingleReal', DataType.SingleReal),
    'CURRENCY': ('Currency', DataType.Currency),
    'STRING': ('String', DataType.String),
    'DATE': ('Date', DataType.Date),
    'TIME': ('Time', DataType.Time),
    'DATETIME': ('DateTime', DataType.DateTime),
    'BOOLEAN': ('Boolean', DataType.Boolean),
    'BINARY': ('Binary', DataType.Binary),
    'VALUE': ('Value', ParameterType.Value),
    'COLUMN': ('Column', ParameterType.Column),
    'TABLE': ('Table', ParameterType.Table)
}

def canonize(ident):
    ident_upper = ident.upper()
    if ident_upper in canonical:
        return canonical[ident_upper][0]
    return ident

def canonize_enum(ident):
    ident_upper = ident.upper()
    if ident_upper in canonical:
        return canonical[ident_upper][1]
    else:
        raise ValueError('No Spotfire enum value for identifier.')

def script_from_filename(fn):
    try:
        f = open(fn)
        return parse(f)
    finally:
        f.close()

# inject (add) a script into the Spotfire Document
def insert_script(script):
    builder = DataFunctionDefinitionBuilder(script.name,
            DataFunctionExecutorTypeIdentifiers.TERRScriptExecutor)
    build_script(script, builder)
    Document.Data.DataFunctions.AddNew(script.display_name, builder.Build())

# replace an existing data function with a script
def replace_script(script, fn):
    builder = DataFunctionDefinitionBuilder(fn.DataFunctionDefinition)
    build_script(script, builder)
    fn.DataFunctionDefinition = builder.Build()

# use a DataFunctionDefinitionBuilder (new or existing) to prepare the
#   script to be built
def build_script(script, builder):
    builder.FunctionName = script.name
    builder.DisplayName = script.display_name
    if script.description is not None:
        builder.Description = script.description
    builder.Settings['script'] = script.script

    builder.InputParameters.Clear()
    for i in script.inputs:
        input_builder = InputParameterBuilder(
                i.name, canonize_enum(i.category))
        input_builder.DisplayName = i.display_name
        input_builder.IsOptional = i.optional
        if i.description is not None:
            input_builder.Description = i.description
        for t in i.allowed_types:
            input_builder.AddAllowedDataType(canonize_enum(t))
        builder.InputParameters.Add(input_builder.Build())

    builder.OutputParameters.Clear()
    for o in script.outputs:
        output_builder = OutputParameterBuilder(
                o.name, canonize_enum(o.category))
        output_builder.DisplayName = o.display_name
        builder.OutputParameters.Add(output_builder.Build())

# find functions likely to need replacement by script
def replace_candidates(script):
    return [df for df in Document.Data.DataFunctions
            if df.Name == script.display_name
            or df.DataFunctionDefinition.FunctionName == script.name]

def get_script_filenames():
    pass

# spotfire "main"
if __name__ == '__builtin__':
    script = script_from_filename(r'C:\Users\Derrick\Desktop\example.R')
    print script
    candidates = replace_candidates(script)
    if not candidates:
        insert_script(script)
    for f in replace_candidates(script):
        replace_script(script, f)
