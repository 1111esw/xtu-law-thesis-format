#!/usr/bin/env python3
"""Set Songti theme roles, Times New Roman Latin slots and empty headers in a copy."""
import argparse
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'w': W, 'a': A}
SPECIAL = {'Symbol', 'Wingdings', 'Wingdings 2', 'Wingdings 3', 'Webdings',
           'Cambria Math', 'MT Extra'}


def w(tag):
    return '{' + W + '}' + tag


def child(parent, tag, first=False):
    elem = parent.find(w(tag))
    if elem is None:
        elem = ET.Element(w(tag))
        parent.insert(0, elem) if first else parent.append(elem)
    return elem


def set_fonts(rpr, role):
    rf = child(rpr, 'rFonts', first=True)
    if any(rf.get(w(slot)) in SPECIAL for slot in ['ascii', 'hAnsi', 'eastAsia']):
        return
    for key in ['asciiTheme', 'hAnsiTheme', 'cstheme', 'csTheme']:
        rf.attrib.pop(w(key), None)
    for slot in ['ascii', 'hAnsi', 'cs']:
        rf.set(w(slot), 'Times New Roman')
    rf.set(w('eastAsia'), '宋体')
    rf.set(w('eastAsiaTheme'), role)
    rf.set(w('hint'), 'eastAsia')
    child(rpr, 'lang').set(w('eastAsia'), 'zh-CN')


def normalize(input_path, output_path):
    if input_path.resolve() == output_path.resolve():
        raise ValueError('Use a different output path; the original must be preserved.')
    changed = {}
    with ZipFile(input_path) as src:
        styles = ET.fromstring(src.read('word/styles.xml'))
        headings = set()
        based = {}
        for st in styles.findall('w:style', NS):
            sid = st.get(w('styleId'), '')
            name = st.find('w:name', NS)
            label = name.get(w('val'), '') if name is not None else ''
            if (sid.lower().startswith(('heading', 'title', 'subtitle')) or
                    label.lower().startswith(('heading', 'title', 'subtitle'))):
                headings.add(sid)
            base = st.find('w:basedOn', NS)
            if base is not None:
                based[sid] = base.get(w('val'))
        while True:
            added = {sid for sid, base in based.items() if base in headings} - headings
            if not added:
                break
            headings.update(added)
        for st in styles.findall('w:style', NS):
            role = 'majorEastAsia' if st.get(w('styleId')) in headings else 'minorEastAsia'
            set_fonts(child(st, 'rPr'), role)
        defaults = child(styles, 'docDefaults', first=True)
        set_fonts(child(child(defaults, 'rPrDefault'), 'rPr'), 'minorEastAsia')
        changed['word/styles.xml'] = styles

        for name in src.namelist():
            if not (name.startswith('word/') and name.endswith('.xml')) or name == 'word/styles.xml':
                continue
            root = ET.fromstring(src.read(name))
            if name.startswith('word/theme/'):
                for family in root.xpath('//a:fontScheme/a:majorFont | //a:fontScheme/a:minorFont', namespaces=NS):
                    for tag, face in [('latin', 'Times New Roman'), ('ea', '宋体')]:
                        el = family.find('a:' + tag, NS)
                        if el is not None:
                            el.set('typeface', face)
                    hans = family.find('a:font[@script="Hans"]', NS)
                    if hans is None:
                        hans = ET.SubElement(family, '{' + A + '}font', script='Hans')
                    hans.set('typeface', '宋体')
                changed[name] = root
            elif name.startswith('word/header'):
                for elem in list(root):
                    root.remove(elem)
                ET.SubElement(root, w('p'))
                changed[name] = root
            elif name == 'word/settings.xml':
                child(root, 'themeFontLang').set(w('eastAsia'), 'zh-CN')
                changed[name] = root
            elif name == 'word/fontTable.xml':
                for font, alt in [('宋体', 'SimSun'), ('Times New Roman', None)]:
                    found = root.find('w:font[@w:name="' + font + '"]', NS)
                    if found is None:
                        found = ET.SubElement(root, w('font'))
                        found.set(w('name'), font)
                    if alt:
                        child(found, 'altName').set(w('val'), alt)
                changed[name] = root
            elif name in ['word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml'] or name.startswith('word/footer'):
                for paragraph in root.iter(w('p')):
                    style = paragraph.find('w:pPr/w:pStyle', NS)
                    sid = style.get(w('val')) if style is not None else None
                    default_role = 'majorEastAsia' if sid in headings else 'minorEastAsia'
                    for run in paragraph.findall('.//w:r', NS):
                        rpr = child(run, 'rPr', first=True)
                        rs = rpr.find('w:rStyle', NS)
                        rsid = rs.get(w('val')) if rs is not None else None
                        set_fonts(rpr, 'majorEastAsia' if rsid in headings else default_role)
                changed[name] = root
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output_path, 'w') as dest:
            for entry in src.infolist():
                content = (ET.tostring(changed[entry.filename], encoding='UTF-8', xml_declaration=True,
                                       standalone=True) if entry.filename in changed else src.read(entry.filename))
                dest.writestr(entry, content)
    return sorted(changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    parts = normalize(args.input, args.out)
    print(f'Updated {len(parts)} XML parts; original preserved. Output: {args.out}')


if __name__ == '__main__':
    main()
