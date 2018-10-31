# from rosetta code
import re
s = '''
(module "16-TFSOP(3.00mm_Width)" (layer F.Cu) (tedit 59C01C2A)
  (fp_text reference REF** (at 0 -3.95) (layer F.SilkS)
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "16-TFSOP(0.118_3.00mm_Width)" (at 0 3.9) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_line (start 2.25 2.8) (end -2.25 2.8) (layer F.CrtYd) (width 0.05))
  (fp_line (start -2.25 -2.8) (end -2.25 2.8) (layer F.CrtYd) (width 0.05))
  (fp_line (start 2.25 -2.8) (end -2.25 -2.8) (layer F.CrtYd) (width 0.05))
  (fp_line (start 2.25 -2.8) (end 2.25 2.8) (layer F.CrtYd) (width 0.05))
  (fp_text user %R (at 0 0) (layer F.Fab)
    (effects (font (size 0.75 0.75) (thickness 0.075)))
  )
  (fp_line (start -2.1 0.9) (end -2.1 1.2) (layer F.SilkS) (width 0.1))
  (fp_line (start -2.1 1.2) (end -2 1.3) (layer F.SilkS) (width 0.1))
  (fp_line (start -2 1.3) (end -2 1.6) (layer F.SilkS) (width 0.1))
  (fp_line (start -2 1.1) (end -2 -1.5) (layer F.Fab) (width 0.1))
  (fp_line (start -1.6 1.5) (end 2 1.5) (layer F.Fab) (width 0.1))
  (fp_line (start -1.6 1.5) (end -2 1.1) (layer F.Fab) (width 0.1))
  (fp_line (start -2 -1.6) (end -2.1 -1.6) (layer F.SilkS) (width 0.1))
  (fp_line (start -2.1 -1.6) (end -2.1 -1.1) (layer F.SilkS) (width 0.1))
  (fp_line (start 2 -1.6) (end 2.1 -1.6) (layer F.SilkS) (width 0.1))
  (fp_line (start 2.1 -1.6) (end 2.1 -1.1) (layer F.SilkS) (width 0.1))
  (fp_line (start 2 1.6) (end 2.1 1.6) (layer F.SilkS) (width 0.1))
  (fp_line (start 2.1 1.6) (end 2.1 1.1) (layer F.SilkS) (width 0.1))
  (fp_line (start -2 1.6) (end -2 2.4) (layer F.SilkS) (width 0.1))
  (fp_line (start 2 -1.5) (end 2 1.5) (layer F.Fab) (width 0.1))
  (fp_line (start -2 -1.5) (end 2 -1.5) (layer F.Fab) (width 0.1))
  (pad 1 smd rect (at -1.75 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 2 smd rect (at -1.25 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 3 smd rect (at -0.75 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 4 smd rect (at -0.25 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 5 smd rect (at 0.25 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 6 smd rect (at 0.75 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 7 smd rect (at 1.25 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 8 smd rect (at 1.75 2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 9 smd rect (at 1.75 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 10 smd rect (at 1.25 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 11 smd rect (at 0.75 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 12 smd rect (at 0.25 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 13 smd rect (at -0.25 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 14 smd rect (at -0.75 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 15 smd rect (at -1.25 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
  (pad 16 smd rect (at -1.75 -2.1) (size 0.3 0.9) (layers F.Cu F.Paste F.Mask))
)


'''
dbg = False
term_regex = r'''(?mx)
    \s*(?:
        (?P<brackl>\()|
        (?P<brackr>\))|
        (?P<dashnum>\d+\-\d+)|
        (?P<num>\-?\d+\.\d+|\-?\d+)|
        (?P<sq>"[^"]*")|
        (?P<s>[^(^)\s]+)
       )'''
 
def parse_sexp(sexp):
    stack = []
    out = []
    if dbg: print("%-6s %-14s %-44s %-s" % tuple("term value out stack".split()))
    for termtypes in re.finditer(term_regex, sexp):
        term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]
        if dbg: print("%-7s %-14s %-44r %-r" % (term, value, out, stack))
        if   term == 'brackl':
            stack.append(out)
            out = []
        elif term == 'brackr':
#             if not stack: 
#                 print('------',term,value)
#                 print(out)
            assert stack, "Trouble with nesting of brackets"
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)
        elif term == 'dashnum':
            out.append(value)
        elif term == 'num':
            v = float(value)
            if v.is_integer(): v = int(v)
            out.append(v)
        elif term == 'sq':
            out.append(value[1:-1])
        elif term == 's':
            out.append(value)
        else:
            raise NotImplementedError("Error: %r" % (term, value))
    assert not stack, "Trouble with nesting of brackets"
    return out[0]
 
def print_sexp(exp):
    out = ''
    if type(exp) == type([]):
        out += '(' + ' '.join(print_sexp(x) for x in exp) + ')'
    elif type(exp) == type('') and re.search(r'[\s()]', exp):
        out += '"%s"' % repr(exp)[1:-1].replace('"', '\"')
    else:
        out += '%s' % exp
    return out