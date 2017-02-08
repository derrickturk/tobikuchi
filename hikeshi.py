# hikeshi
# dump data functions from an existing project in a format tobikuchi can read
# (c) 2017 dwt | terminus data science, LLC

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import clr
clr.AddReference('System.Windows.Forms')

from System.IO import Path
from System.Windows.Forms import FolderBrowserDialog, DialogResult

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
    # Spotfire likes to give every function the FunctionName 'Untitled'
    stream.write('# TK_FN %s\n' % (builder.FunctionName
        if builder.FunctionName != 'Untitled'
        else builder.DisplayName
    ))
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
    stream.write(builder.Settings['script'].replace('\r', ''))
    if not builder.Settings['script'].endswith('\n'):
        stream.write('\n')

def get_output_directory():
    folder_dialog = FolderBrowserDialog()
    folder_dialog.ShowNewFolderButton = True
    folder_dialog.Description = 'Output directory for R scripts'
    if folder_dialog.ShowDialog() != DialogResult.OK:
        return None
    return folder_dialog.SelectedPath

def make_filename(df):
    return df.Name + '.R'

def report_error(fn, err):
    MessageBox.Show('Error processing %s:\n%s' % (fn, err),
            'tobikuchi error', MessageBoxButtons.OK, MessageBoxIcon.Error)

# spotfire "main"
import sys
output_dir = get_output_directory()
if output_dir is not None:
    for df in Document.Data.DataFunctions:
        fn = make_filename(df)
        try:
            f = open(Path.Combine(output_dir, fn), 'w')
            dump_function(df, f)
        except Exception, e:
            report_error(fn.Name, e)
        finally:
            f.close()
