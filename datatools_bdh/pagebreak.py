#!/usr/bin/env python

"""
pagebreak.py
A pandoc filter that converts certain HTML div tags into docx pagebreaks.

"""

from pandocfilters import toJSONFilter, Str, Para, RawBlock
import re

# Below is the secret sauce, originating from a Haskell script in https://github.com/alexstoick/pandoc-docx-pagebreak
pagegBreakLandscapeXml = "<w:p><w:pPr><w:sectPr> <w:pgSz w:w=\"15840\" w:h=\"12240\"  w:orient=\"landscape\" /></w:sectPr></w:pPr></w:p>"
pageBreakXml = "<w:p><w:pPr><w:sectPr> <w:pgSz w:w=\"12240\" w:h=\"15840\"/> </w:sectPr></w:pPr></w:p>"

def html(x):
    return RawBlock('html', x)

def xml(x):
    return RawBlock('openxml', x)

def write_pb_docxtpl(landscape=False):
  #landscape not implemented via docxtpl
  return [Para([Str('{{ "\\f" }}')])]

def write_pb_docx(landscape=False):
  if landscape:
    return xml(pagegBreakLandscapeXml)
  else:
    return xml(pageBreakXml)

#write_pb = write_pb_docxtpl
write_pb = write_pb_docx

def pagebreak(key, value, format, meta):
  try:
    if key == 'Div':
      [[ident, classes, kvs], contents] = value
      kvd = dict(kvs)
      if re.search(r'page-break-after *: *always', kvd['style']):
        return write_pb(landscape=False)
      elif re.search(r'page-break-landscape-after *: *always', kvd['style']):
        return write_pb(landscape=True)
  except KeyError:
    pass

if __name__ == "__main__":
  toJSONFilter(pagebreak)
