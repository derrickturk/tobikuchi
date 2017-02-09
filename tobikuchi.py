# tobikuchi
# a pointy stick for fighting (spot) fires
# (c) 2017 dwt | terminus data science, LLC

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

import clr
clr.AddReference('System.Windows.Forms')

from System.Windows.Forms import OpenFileDialog, DialogResult
from System.Windows.Forms import MessageBox
from System.Windows.Forms import MessageBoxIcon, MessageBoxButtons

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
        self.aliases = []
        self.allow_caching = True
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
            raise ValueError('Duplicate input name: ' + input.name)
        self.inputs.append(input)
        self._describe_next = input

    def add_output(self, output):
        if output.name in (o.name for o in self.outputs):
            raise ValueError('Duplicate output name: ' + output.name)
        self.outputs.append(output)
        self._describe_next = output

    # add a description line to whatever is currently 'ready for description'
    #   i.e. first the script, then each input and output in turn, when doing
    #   a linear parse
    def describe_next(self, line):
        self._describe_next.add_description_line(line)

    def add_alias(self, alias):
        self.aliases.append(alias)

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
                raise ValueError('Invalid TK command: ' + command)
            handlers[command](script, line[match.span()[1]:].lstrip())
        script.add_script_line(line)

    if script.name is None:
        raise ValueError('Not a TK-annotated script (missing TK_FN).')

    return script
parse.annotation_re = re.compile(r'^\s*#\s*TK_(\w+)', re.I)

def parse_fn_name(script, line):
    script.name = line.rstrip()

def parse_fn_display_name(script, line):
    script.display_name = line.rstrip()

def parse_input(script, line):
    match = parse_input.input_re.match(line)
    if not match:
        raise ValueError('Invalid input description: ' + line)

    input = Input()
    input.name = match.group(1)

    if match.group(5) is not None:
        input.display_name = match.group(5).strip()

    if match.group(6) is not None:
        input.optional = True

    input.category = canonize(match.group(7))

    types = list(map(lambda s: canonize(s.strip()), match.group(8).split('|')))
    bad_types = list(filter(lambda t: t not in valid_types, types))
    if bad_types:
        raise ValueError('Invalid input type: ' + ', '.join(bad_types))
    input.allowed_types = types

    script.add_input(input)
parse_input.input_re = re.compile(r'(((\.[_A-Za-z])|[A-Za-z])[._A-Za-z0-9]*)' +
        r'\s*({([^}]*)})?\s*::\s*(Optional)?\s*(Value|Column|Table)\s+of\s+' +
        r'(\w+(\s*\|\s*\w+)*)', re.I)

def parse_output(script, line):
    match = parse_output.output_re.match(line)
    if not match:
        raise ValueError('Invalid output description: ' + line)
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

def parse_alias(script, line):
    script.add_alias(line.rstrip())

def parse_nocache(script, line):
    if line.strip():
        raise ValueError('Additional arguments to TK_NOCACHE.')
    script.allow_caching = False

handlers = {
    'FN': parse_fn_name,
    'DN': parse_fn_display_name,
    'IN': parse_input,
    'OUT': parse_output,
    'DESC': parse_description,
    'AKA': parse_alias,
    'NOCACHE': parse_nocache
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
        raise ValueError('Identifier not recognized: ' + ident)

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
    builder.AllowCaching = script.allow_caching
    if script.description is not None:
        builder.Description = script.description.replace('\n', '\r\n')
    builder.Settings['script'] = script.script

    builder.InputParameters.Clear()
    for i in script.inputs:
        input_builder = InputParameterBuilder(
                i.name, canonize_enum(i.category))
        input_builder.DisplayName = i.display_name
        input_builder.IsOptional = i.optional
        if i.description is not None:
            input_builder.Description = i.description.replace('\n', '\r\n')
        for t in i.allowed_types:
            input_builder.AddAllowedDataType(canonize_enum(t))
        builder.InputParameters.Add(input_builder.Build())

    builder.OutputParameters.Clear()
    for o in script.outputs:
        output_builder = OutputParameterBuilder(
                o.name, canonize_enum(o.category))
        output_builder.DisplayName = o.display_name
        if o.description is not None:
            output_builder.Description = o.description.replace('\n', '\r\n')
        builder.OutputParameters.Add(output_builder.Build())

# find functions likely to need replacement by script
def replace_candidates(script):
    return [df for df in Document.Data.DataFunctions
            if df.Name == script.display_name
            or df.DataFunctionDefinition.FunctionName == script.name
            or df.Name in script.aliases
            or df.DataFunctionDefinition.FunctionName in script.aliases]

# get user-selected set of filenames
def get_script_filenames():
    file_dialog = OpenFileDialog()
    file_dialog.Filter = 'R scripts (*.R)|*.R|All files (*.*)|*.*'
    file_dialog.Multiselect = True
    if file_dialog.ShowDialog() != DialogResult.OK:
        return []
    return list(file_dialog.FileNames)

def report_error(fn, err):
    MessageBox.Show('Error processing %s:\n%s' % (fn, err),
            'tobikuchi error', MessageBoxButtons.OK, MessageBoxIcon.Error)

# spotfire "main"
script_files = get_script_filenames()
for fn in script_files:
    try:
        script = script_from_filename(fn)
        candidates = replace_candidates(script)
        if not candidates:
            insert_script(script)
        for f in replace_candidates(script):
            replace_script(script, f)
    except Exception, e:
        report_error(fn, e)
