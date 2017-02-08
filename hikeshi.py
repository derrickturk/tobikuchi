from Spotfire.Dxp.Data.DataFunctions import *

def dump_function(df, stream):
    builder = DataFunctionDefinitionBuilder(df.DataFunctionDefinition)
    dump_header(builder, stream)
    for ip in builder.InputParameters:
        dump_input(ip, stream)
    for op in builder.OutputParameters:
        dump_output(op, stream)
    dump_script(builder, stream)

def dump_header(builder, stream):
    stream.write('# TK_FN %s\n' % builder.FunctionName)
    stream.write('# TK_DN %s\n' % builder.DisplayName)
    if builder.Description:
        for line in builder.Description.split('\n'):
            stream.write('# TK_DESC %s\n' % line)

def dump_input(ip, stream):
    stream.write('# TK_IN %s%s :: %s%s of %s\n' % (
        ip.Name,
        ' { ' + ip.DisplayName + ' }' if ip.DisplayName else '',
        'Optional ' if ip.IsOptional else '',
        ip.ParameterType.ToString(),
        ' | '.join(dt.ToString() for dt in ip.AllowedDataTypes)
    ))
    if ip.Description:
        for line in ip.Description.split('\n'):
            stream.write('# TK_DESC %s\n' % line)

def dump_output(op, stream):
    stream.write('# TK_OUT %s%s :: %s\n' % (
        op.Name,
        ' { ' + op.DisplayName + ' }' if op.DisplayName else '',
        op.ParameterType.ToString()
    ))
    if op.Description:
        for line in op.Description.split('\n'):
            stream.write('# TK_DESC %s\n' % line)

def dump_script(builder, stream):
    stream.write(builder.Settings['script'])
    if not builder.Settings['script'].endswith('\n'):
        stream.write('\n')

import sys
for df in Document.Data.DataFunctions:
    dump_function(df, sys.stdout)
