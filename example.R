# TK_FN MysteryTERRFn
# TK_DN Mysterious TERR Function
# TK_DESC It's a mysterious TERR Function, really, which does a few things.
# TK_DESC We'd like to support multi-line descriptions as well.
# TK_IN in1 { Input #1 } :: Value of Real | SingleReal
# TK_IN in2 { Input #2 } :: Column of Integer
# this next input doesn't have a display name
# TK_IN in3 :: Optional Value of String
# TK_OUT out { Output } :: Table
# TK_DESC This is an output table.

MysteryTERRFn <- function(in1, in2, in3)
{
    data.frame(scalar=in1, values=in1 * in2, names=in3,
      stringsAsFactors=FALSE)
}

if (length(in3 == 0))
    in3 <- "None"

out <- MysteryTERRFn(in1, in2, in3)
