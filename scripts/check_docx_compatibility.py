#!/usr/bin/env python3
"""Read-only font/header evidence for a DOCX; no application rendering claims."""
import argparse
import ctypes
import json
import re
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'


def system_font_resolution(names):
    if sys.platform != 'darwin':
        return {'available': False, 'reason': 'macOS-only system lookup'}
    cf = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    ct = ctypes.CDLL('/System/Library/Frameworks/CoreText.framework/CoreText')
    cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    cf.CFStringCreateWithCString.restype = ctypes.c_void_p
    cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
    cf.CFStringGetCString.restype = ctypes.c_bool
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    ct.CTFontCreateWithName.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_void_p]
    ct.CTFontCreateWithName.restype = ctypes.c_void_p
    for fn in ['CTFontCopyFamilyName', 'CTFontCopyPostScriptName']:
        getattr(ct, fn).argtypes = [ctypes.c_void_p]
        getattr(ct, fn).restype = ctypes.c_void_p

    def read_string(ptr):
        buf = ctypes.create_string_buffer(4096)
        try:
            if not cf.CFStringGetCString(ptr, buf, len(buf), 0x08000100):
                raise RuntimeError('Unable to decode font name')
            return buf.value.decode('utf-8')
        finally:
            cf.CFRelease(ptr)

    result = {}
    for name in sorted(names):
        s = cf.CFStringCreateWithCString(None, name.encode('utf-8'), 0x08000100)
        font = ct.CTFontCreateWithName(s, 12, None)
        try:
            result[name] = {
                'resolved_family': read_string(ct.CTFontCopyFamilyName(font)),
                'resolved_postscript': read_string(ct.CTFontCopyPostScriptName(font)),
            }
        finally:
            cf.CFRelease(font)
            cf.CFRelease(s)
    return {'available': True, 'fonts': result,
            'scope': 'System name resolution only; application-private fonts are not checked.'}


def inspect_docx(path):
    report = {'file': str(path.resolve()), 'headers_with_content': [], 'theme_font_roles': {},
              'font_declarations': {}, 'theme_font_attribute_count': 0}
    declared_names = {'宋体', 'SimSun', 'Times New Roman'}
    with ZipFile(path) as archive:
        if 'word/document.xml' not in archive.namelist():
            raise ValueError('Not a Word DOCX package')
        for name in archive.namelist():
            if not (name.startswith('word/') and name.endswith('.xml')):
                continue
            root = ET.fromstring(archive.read(name))
            if name.startswith('word/theme/'):
                role_fonts = {}
                for role in ['majorFont', 'minorFont']:
                    family = root.find('.//' + A + 'fontScheme/' + A + role)
                    if family is not None:
                        entry = {}
                        for slot in ['latin', 'ea']:
                            element = family.find(A + slot)
                            entry[slot] = element.get('typeface') if element is not None else None
                        entry['Hans'] = next((e.get('typeface') for e in family.findall(A + 'font')
                                              if e.get('script') == 'Hans'), None)
                        role_fonts[role] = entry
                report['theme_font_roles'][name] = role_fonts
            fonts = Counter()
            for elem in root.iter(W + 'rFonts'):
                for key, val in elem.attrib.items():
                    slot = key.rsplit('}', 1)[-1]
                    if slot in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
                        fonts[f'{slot}={val}'] += 1
                        declared_names.add(val)
                    if slot.endswith('Theme'):
                        report['theme_font_attribute_count'] += 1
            if fonts:
                report['font_declarations'][name] = dict(sorted(fonts.items()))
            if re.fullmatch(r'word/header[^/]*\.xml', name):
                text = ''.join(e.text or '' for e in root.iter(W + 't')).strip()
                nontext = sorted({e.tag.rsplit('}', 1)[-1] for e in root.iter()
                                  if e.tag in [W + 'drawing', W + 'pict', W + 'object',
                                               W + 'fldChar', W + 'fldSimple', W + 'instrText']})
                borders = list(root.iter(W + 'pBdr')) + list(root.iter(W + 'tblBorders'))
                visible_borders = [b for b in borders if any(
                    child.attrib.get(W + 'val', 'single') not in ['nil', 'none'] for child in b)]
                if text or nontext or visible_borders:
                    report['headers_with_content'].append({
                        'part': name, 'text': text, 'other_content': nontext,
                        'visible_border_count': len(visible_borders)})
        if 'word/fontTable.xml' in archive.namelist():
            fonts = ET.fromstring(archive.read('word/fontTable.xml'))
            report['font_table_names'] = [e.get(W + 'name') for e in fonts.iter(W + 'font')]
    report['system_font_resolution'] = system_font_resolution(declared_names)
    report['limits'] = ('Declared fonts only, without complete style inheritance resolution. '
                        'No WPS/Word rendering verification; an empty header report does not '
                        'check linked text boxes outside header parts.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_docx(args.docx), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
