#!/usr/bin/env python3
from xml.dom import minidom
from html import unescape
import re
from utils import sanitize, line_rules, download

# TODO:     ['−', '-']  # replace unicode minus sign with hypen-minus (the minus commonly used on computer keyboard)
# TODO: sentences with different alphabets

DOWNLOAD_PATH = 'https://dumps.wikimedia.org/itwikiquote/latest/itwikiquote-latest-pages-articles.xml.bz2'
OUTFILE = "output/wikiquote.txt"
DISCARD_FILE = 'output/discarded/wikiquote.json'

download_me = download.Download()
validate_line = line_rules.LineRules(discard_file=DISCARD_FILE)
clean_me = sanitize.Sanitization()

sub_regex = re.compile(r"""\[\[(File|Category):[\s\S]+\]\]|
                        \[\[[^|^\]]+\||
                        \[\[|\]\]|
                        \'{2,5}|
                        (<s>|<!--)[\s\S]+(</s>|-->)|
                        (<s>|<!)[\s\S]+(</s>|>)|
                        {{[\s\S\n]+?}}|
                        <.*?>|
                        ={1,6}""", re.VERBOSE)

normalize_rules = [['*', u"\n"],
                   ['<br />', u"\n"],
                   ['<br>', u"\n"],
                   ["\(\d\d\d\d\)", ""],
                   ["[\(\[].*?[\)\]]", ""],
                   ['AvvertenzaContattiDonazioni', ''],
                   [re.compile("^[eE]'"),"è"]
                   ]
words_blacklist = ['|', '{{', ':', '[', 'ISBN', '#', 'REDIRECT', 'isbn', 'RINVIA', 'thumb', 'right', 'Citato', ', citato', '; citato']

# titles_blacklist = [
#         "Modulo:Arguments/man",
#         "Modulo:Arguments",
#         "Modulo:Wikidata/Sandbox/man",
#         "Modulo:Wikidata",
#         "Modulo:Wikidata/man",
#         "Wikiquote:Elenchi generati offline/Immagini in Wikiquote e Wikipedia/Elenco 2",
#         "Wikiquote:Elenchi generati offline/Immagini in Wikiquote e Wikipedia/Elenco 1"
# ]
def process_page(page, out_file):
    title = page.getElementsByTagName("title")[0].firstChild.data
    tot_lines = 0
    # pages with titles containing ":" are not so clean
    if ":" not in title and 'wiki' not in title and title != 'Pagina principale' and 'MediaWiki' not in title:
        format_elem = page.getElementsByTagName("revision")[0].getElementsByTagName("format")[0]
        if format_elem.firstChild.data == 'text/x-wiki':
            textdom = page.getElementsByTagName("revision")[0].getElementsByTagName("text")[0]
            if textdom.firstChild is not None:
                raw_text = unescape(textdom.firstChild.data)
                raw_text = sub_regex.sub("", raw_text)
                raw_text = clean_me.maybe_normalize(raw_text, normalize_rules, False)
                lines = clean_me.prepare_splitlines(raw_text).splitlines()
                for line in lines:
                    if process_line(line, out_file):
                        tot_lines += 1
    return tot_lines


def process_line(line, out_file):
    """if line is invalid returns early, if is correct writes the line to the file"""
    # line = clean_me.clean_single_line(line).strip()
    # # to debug strange sentences
    # if "L'uomo o impazzisce o scrive" in line:
    #     print(line)

    # Some lines starts with E' verb
    line = re.sub("^[eE]'", "è", line)
    # Lot of lines with these
    line = re.sub(r"AA\. |VV |VV\.|AA\.VV", "", line)
    if (validate_line.is_not_valid(line) or
            len(line) <= 15
            or validate_line.startswith(line, ['(', 'vivente)']) or
            validate_line.contain(line, words_blacklist) or
            # validate_line.isdigit([line, line[1:], line[:1]]) or commented out because with the current regex digits and brackets are always discarded
            validate_line.isbookref(line) ):
            # validate_line.isbrokensimplebracket(line)
        return False
    else:
        out_file.write(line + "\n")
        return True


def main():
    print('Reading XML file')
    xml_path = download_me.if_not_exist(DOWNLOAD_PATH).bz2_decompress()
    mydoc = minidom.parse(xml_path)

    items = mydoc.getElementsByTagName('page')

    out_file = open(OUTFILE, 'w')
    print('Processing lines')
    tot_lines = 0
    for page in items:
        tot_lines += process_page(page, out_file)
    out_file.close()

    print("Total number of line processed: ", tot_lines)

    validate_line.save()

if __name__ == "__main__":
    main()
