# tobikuchi
## a pointy stick for fighting (spot) fires
### by [dwt](https://github.com/derrickturk) | [terminus data science, LLC](https://www.terminusdatascience.com)

tobikuchi is a simple tool for managing TERR (R) data functions in TIBCO Spotfire. As a "visual analytics" tool, Spotfire falls into the ever-growing category of "secret development platforms beloved by end-users but hated by programmers, with absolutely no sensible source file management nor build system".

Well, thank God for their automation API, then.

tobikuchi uses special R comments beginning with `# TK_` to understand a data function, including its name, description, inputs, and outputs.
The full set of commands is described below; optional elements are indicated in `[braces]`; these braces do not appear in actual code.
All commands are case-insensitive.

|Command     |Description   |Syntax                                                                                |
|---------  -|--------------|--------------------------------------------------------------------------------------|
|`TK_FN`     |Function name |`# TK_FN MyTERRFunction`                                                              |
|`TK_DN`     |Display name  |`# TK_DN Display Name of My Function`                                                 |
|`TK_DESC`   |Description   |`# TK_DESC This function does things...`                                              |
|`TK_IN`     |Input         |`# TK_IN name [{ display name }] :: [Optional] Category of Type1 [| Type2]...`        |
|`TK_OUT`    |Output        |`# TK_OUT name [{ display name }] :: Category`                                        |
|`TK_AKA`    |Alias name    |`# TK_AKA Old Name of Function`                                                       |
|`TK_NOCACHE`|Forbid caching|`# TK_NOCACHE`                                                                        |

The only required element is `TK_FN`, to give each function a name.

The Category for an input or output may be `Value`, `Column`, or `Table`; the Type(s) for an input may be any Spotfire type (e.g. `Real`, `String`...).

`TK_DESC` description lines are cumulative; each `TK_DESC` entry will add a line to the description of the "currently described entity", which is the function itself until the first input or output is encountered; subsequently the "currently described entity" is the last input or output definition processed.

`TK_AKA` alias lines are used to allow transition of old projects to tobikuchi; scripts may declare alias names for matching against existing data functions. A new script definition will replace any data function whose display name or function name matches one of its aliases.

See [`example.R`](example.R) for a short example of tobikuchi command syntax.

To use tobikuchi, add the contents of [`tobikuchi.py`](tobikuchi.py) as an IronPython script to a Spotfire project; when executed, it will launch a dialog for picking R script files.
These files will be parsed as described above; when (function or display) names can be matched to existing data functions, these functions will be updated in-place. Otherwise, new functions will be added to the project.

A supplementary tool, hikeshi, may be used to export data function definitions from an existing Spotfire project to .R files with tobikuchi command comments. To use hikeshi, add the contents of [`hikeshi.py`](hikeshi.py) as an IronPython script to the Spotfire project. When executed, hikeshi will launch a dialog allowing selection of a directory into which the .R files (with names taken from the data functions' display names) will be written.

### Available for commercial or non-commercial use under the Mozilla Public License Version 2.0
### (c) 2017 [dwt](https://github.com/derrickturk) | [terminus data science, LLC](https://www.terminusdatascience.com)
