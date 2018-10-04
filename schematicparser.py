from pyparsing import *
import pprint


dot = Literal(".")
quote = Literal('"')
octothorp = Literal('#')
dash = Literal('-')
soct = Suppress(octothorp)
# soct = (octothorp)
# qword = nestedExpr(
#   Literal('"'),
#   OneOrMore(~Literal('"') + Word(printables)),
#   Literal('"')
#   )
qword = quotedString()
snums = Word(nums+'-')
slineEnd = Suppress(lineEnd)
#EESchema-DOCLIB  Version 2.0  Date: 21/01/2011 13:15:12
# date = Keyword('Date:')+ Word(nums+'/') + Word(nums+':')
date = restOfLine

version = Combine(Word(nums) + dot + Word(nums))
libstart = Suppress("EESchema-LIBRARY Version")+version('version') + Optional(date)
libend = octothorp +Keyword("#End Library")+lineEnd

encoding = (
  Suppress('#encoding') 
  + Combine( Word(alphas) + Optional( Word('-'+nums) ) )
).setResultsName('encoding')

def incomplete():
  print('incomplete'+libraries)

##parse dcm
## check consistency of pin count on sybols to pad count on footprint
## write a simple sanity check functoin to count ENDDEFS in file and compare to parsed results


class Symbols:
# symbol definitions
# note Digi-Key partnumbers can technically have spaces in them.  That case is ingored throughout
    preamble = soct + soct + Word(printables).setResultsName('partnumber') + soct    
    name = Word(printables)
    ref = Word(printables)
    zero = Literal("0")
    offset = Word(nums+'-')
    showpins = Word('YN')
    showpinnames = Word('YN')
    fracturecount = Word(nums)
    locked = MatchFirst([Word('LF'), Word('0').setParseAction(lambda : print('invalid locked value'))])  #optional
    power = Word('PN') #optional
    defline = Word("DEF")+ name + ref + zero + offset + showpins + showpinnames + fracturecount + Optional(locked)+ Optional(power)+Suppress(LineEnd())
    
    
textx = snums
texty = snums
textsize = snums
textorientation = Word('VH')
invisible = Word('IV')
halignment = Word('CLRTB', exact=1)
valignment = Word('CLRTB', exact=1)
italic = Word('IN', exact=1)
bold = Word('BN', exact=1)
footprintname = Word(printables)
datasheetpath = Word(printables)
fieldname = quotedString()

#Fn fields
s = Symbols()
# print(s.defspot)
# Fn = Group(
#       Combine(Literal("F")+Word(nums))  
#       + qword 
#       + textx 
#       + texty 
#       + textsize 
#       + textorientation 
#       + invisible 
#       + halignment 
#       + valignment 
#       + italic 
#       + bold 
#       + MatchFirst( [Suppress(lineEnd), fieldname + Suppress(lineEnd)])
# )

Fn = Group(
      Combine(Literal("F")+Word(nums))('fnum')  
      + qword('fvalue')
      + textx('x') 
      + texty('y') 
      + textsize('textsize') 
      + textorientation('textorient') 
      + invisible('visible') 
      + halignment('halign') 
      + valignment('valign') 
      + italic('italic') 
      + bold('bold') 
      + MatchFirst( [Suppress(lineEnd), fieldname('field') + Suppress(lineEnd)])('fieldname')
)('fnitem')


Fns = Group(
  MatchFirst(
    [Fn('F0') +Fn('F1') +Fn('F2') +Fn('F3')  + ZeroOrMore(Fn),
      ZeroOrMore(Fn).setParseAction(lambda : print('Missing F lines'))
    ])
  ).setResultsName('fns')

class Arc:
    #arc
    x = snums
    y = snums
    start = snums
    end = snums
    dmg = nums
    pen = nums
    fill = Word('fFN')
    xstart = snums
    ystart = snums
    xend = snums
    yend = snums
    
class Circle:
    pass

# fplist = (
#   Keyword('$FPLIST')
#   + OneOrMore(Word(printables))  #TEST against multiple aliases
#   + Keyword('$ENDFPLIST') 
# ).setResultsName('fplist')

alias = (
  Suppress(Keyword("ALIAS"))
  + Word(printables)
  # + lineEnd
  + MatchFirst(
      lineEnd, 
      OneOrMore(Word(printables))+lineEnd
    )
) #check if alias can have spaces or multiples

alias2 = (
  Suppress(Keyword("ALIAS"))
  + OneOrMore(~Literal("DRAW")+ ~Literal("$FPLIST") + Word(printables))
  + lineEnd
  # + MatchFirst(
  #     lineEnd, 
  #     OneOrMore(Word(printables))+lineEnd
  #   )
)

fpopener = Keyword('$FPLIST')
fpcloser = Keyword('$ENDFPLIST')
# fpcontent = OneOrMore(~fpopener + ~fpcloser + Word(printables))
fpcontent = OneOrMore(Word(printables))
#.setParseAction(debugparser)
fplist = nestedExpr(
  fpopener,
  fpcloser,
  fpcontent
  # .setParseAction(debugparser)
)

fplist2 = fpopener + OneOrMore(~fpopener + ~fpcloser + Word(printables)) + fpcloser
def debugparser(s, loc, toks):
  # pass
  print(toks, loc)

partparser = Group(
    s.preamble
    + s.defline('def')
    + Fns('fns')
    + Optional(alias2)('alias')   #check if can have multiples
    + Optional(fplist2)('fplist')
    + Keyword("DRAW")
    + SkipTo(Keyword('ENDDRAW'),include=True)('draw')
    + Keyword('ENDDEF')
)

libraryparser = (
    libstart 
    + Optional(encoding)
    + Group(OneOrMore(partparser)).setResultsName('parts')

    + libend
) 

docstart = Suppress('EESchema-DOCLIB  Version ') + version +MatchFirst([restOfLine + Suppress(octothorp),Suppress(octothorp)])
CMP = Suppress(Literal('$CMP'))+Word(printables)
# description = Literal('D')+ restOfLine
# description = Literal('K')+ restOfLine
# description = Literal('F')+ restOfLine
# description = Literal('D')+ Combine(OneOrMore(Word(printables))) + slineEnd
# keywords = Literal('K')+ Combine(OneOrMore(Word(printables))) + slineEnd
# keywords = Literal('K')+ Combine(OneOrMore(Word(printables))) + slineEnd
# datasheetfile = Literal('F')+ Combine(OneOrMore(Word(printables))) + slineEnd
# datasheetfile = Literal('F')+ Combine(OneOrMore(Word(printables))) + slineEnd
ENDCMP = Suppress(Keyword('$ENDCMP') + octothorp +(Optional(octothorp+lineEnd)) )
docend = Suppress('#End Doc Library')


def toKeyValue(toks):
  return {toks[0]:toks[1:][0].strip()}


docparser = (
  docstart('docstart') 
  + Group(
      ZeroOrMore(Group(
        CMP('pn')
        # + Group(OneOrMore(Group(Word("DKF")('doctype')+restOfLine('docinfo'))))('doclines')
        + Group(OneOrMore((Word("DKF")('doctype')+restOfLine('docinfo')).setParseAction(toKeyValue)))('doclines')

        + ENDCMP 
      ))
    )('partlist')
  + docend('docend')
)('docparse')


# ppversion = pyparsing.__version__