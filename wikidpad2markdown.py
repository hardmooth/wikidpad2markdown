# -*- coding: utf-8 -*-
"""
script to migrate from wikidpad to markdown (and possibly upload to confluence)
@copyright:   Hartmut Leister, 2023, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import difflib
import glob
import logging
import os
import re
import sys
import traceback
from itertools import zip_longest
from optparse import OptionParser

# -- pip ---
try:
    import markdown
except ImportError:
    # no markdown installed. we can still work partly without
    markdown = None

try:
    # load the confluence cloud Rest API helper
    # see https://atlassian-python-api.readthedocs.io/
    from atlassian import confluence
except ImportError:
    confluence = None

try:
    import mistune
    from md2cf.confluence_renderer import ConfluenceRenderer
except ImportError:
    mistune = None
    ConfluenceRenderer = None


# -- local imports ---
from diffhelper import better_diff

EXIT_OK                = 0
EXIT_BAD_PARAMETERS    = 1
EXIT_BAD_PREREQUISITES = 2
EXIT_CRITICAL          = 4 

#: log file to write to (wikidpad2markdown.log in the current working directory)
LOG_FILE = os.path.join( os.getcwd(), os.path.basename( __file__).rstrip("pyco") + "log")
_logger = logging.getLogger()
def loggingSetup( log_file, print_to_stdout = True):
    # reset log file if already existed
    if os.path.exists(log_file):
        os.remove(log_file)

    formatter = logging.Formatter( '%(asctime)s [%(levelname)s] %(message)s')
    _logger.setLevel( logging.DEBUG)

    # log to file
    file_handler = logging.FileHandler( filename= log_file)
    file_handler.setLevel( logging.DEBUG)
    file_handler.setFormatter( formatter)
    _logger.addHandler( file_handler)

    # 
    if print_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel( logging.INFO)
        stdout_handler.setFormatter( formatter)
        _logger.addHandler( stdout_handler)

_CONFLUENCE_CONNECTION = None
def ParseOptions( options = None, args = None, **kwargs):
    global _CONFLUENCE_CONNECTION

    parser = OptionParser()
    parser.add_option("-w", "--wikidpad", dest="wikidpad_files", help="Input Wikidpad files (may be globular expression)", default="_sample_pages/*.wiki")
    parser.add_option("-o", "--out",      dest="output_dir",    help="Output directory for generated Markdown files", default="out")

    parser.add_option("-V", "--verify", dest="verify", action="store", default=None, help="Verify created Markdown files against those in the given directly (for each'file.wiki' there must be 'file.md'")
    parser.add_option("-R", "--render", dest="render", action="store_true", default="False", help="Render transformed files to HTML as well.")

    parser.add_option("--confluence-url", dest="ConfluenceURL", action="store", help = "Confluence upload: URL of confluence cloud instance")
    parser.add_option("--confluence-space", dest="ConfluenceSpace", action="store", help = "Confluence upload: Space Key")
    parser.add_option("--confluence-user", dest="ConfluenceUser", action="store", help = "Confluence upload: Name of user")
    parser.add_option("--confluence-parent-id", dest="ConfluenceParentID", action="store", help="Confluence upload: (optional) ID of parent page")
    parser.add_option("--confluence-token", dest="ConfluenceAPIToken", action="store", help = "Confluence upload: Confluence API Token")

    # TODO: disable
    parser.add_option("-s", "--strict", dest="Strict", action="store_true", default=True, help="Abort on the first error (or keep going?).")

    ##################################################################################
    # adapt set parameters according to passed arguments, e.g. when used as a module #
    ##################################################################################

    if options is None:
        options, args =  parser.parse_args(sys.argv)
    elif isinstance(options, str):
        options, args =  parser.parse_args([options, args])
    elif isinstance(options, dict):
        _opts = options
        options, args =  parser.parse_args([u''])
        options.__dict__.update(_opts)
    elif isinstance(options, tuple):
        options, args = options

    options.__dict__.update(kwargs)

    ###################################
    # check some options for validity #
    ###################################
    if markdown is None and options.render:
        logging.warning( "'markdown' package is not installed. Generating HTML from markdown will fail ")


    if any( [options.ConfluenceURL, options.ConfluenceSpace, options.ConfluenceUser, options.ConfluenceAPIToken, ]):
        _CONFLUENCE_CONNECTION = confluence.Confluence(
            url=options.ConfluenceURL,
            username=options.ConfluenceUser,
            password=options.ConfluenceAPIToken,
            cloud=True
        )
        logging.info("Confluence upload mode enabled. Connecting to %s: %s", options.ConfluenceURL, _CONFLUENCE_CONNECTION)

        if mistune is None or ConfluenceRenderer is None:
            logging.warning("'md2cf' package is missing. Correct Confluence output can't be guaranteed")


    return options, args

def diff_texts(text1, text2, title1 = "A", title2 = "B", skip_equal = True, ignore_whitespacing = False):
    lines1 = text1.splitlines() if isinstance( text1, str) else text1
    lines2 = text2.splitlines() if isinstance( text2, str) else text2

    # Ignore changes in whitespacing
    def reduce_whitespaces(line):
        return ' '.join(line.split())
    
    if ignore_whitespacing:
        lines1 = list(map(reduce_whitespaces, lines1))
        lines2 = list(map(reduce_whitespaces, lines2))

    differ = difflib.Differ()
    diff = list(differ.compare(lines1, lines2))
    
    max_len = max(len(line) for line in lines1+lines2)
    column_width = max(max_len + 3, 20)
    
    result = []
    left_line_num = 1
    right_line_num = 1
    left_lines = []
    right_lines = []
    
    for i, line in enumerate(diff):
        line = line.rstrip()
        if line.startswith('+ '):
            right_lines.append(f"{right_line_num:3}: {line[2:]:<{column_width}}")
            right_line_num += 1
        elif line.startswith('- '):
            left_lines.append(f"{left_line_num:3}: {line[2:]:<{column_width}}")
            left_line_num += 1
        elif line.startswith('  '):
            if not skip_equal:
                left_lines.append(f"{left_line_num:3}: {line[2:]:<{column_width}}")
                right_lines.append(f"   {'':<{column_width}}| {line[2:]:<{column_width}}")
            left_line_num += 1
            right_line_num += 1
    
    # pad with 5 chars for column prefix (line number and spaces)
    column_width += 5
    
    if left_lines or right_lines:
        # add title and separator 
        left_lines  = [ f"{title1:<{column_width}}", "-"*(column_width)] + left_lines 
        right_lines = [ f"{title2:<{column_width}}", "-"*(column_width)] + right_lines

    for left_line, right_line in zip_longest(left_lines, right_lines, fillvalue=' '*column_width):
        result.append(f"{left_line} | {right_line}")
    
    return '\n'.join(result)


def Wikidpad2Markdown(wiki_source, remove_remaining_wikidpad = True):
    """Converts Wikidpad to Markdown syntax.
    Generated from conversation with ChatGPT

    Args:
        wiki_source (_type_): _description_

    Returns:
        _type_: _description_
    """
    def table_add_header( table_block_match):
        table_source = table_block_match.group(0)
        rows = table_source.splitlines()
        first_row = rows[0]
        col_count = rows[0].count("|") - 1
        return "\n".join([
            first_row,
            "| -- " * col_count + "|",
            ] + rows[1:])


    # Replace headings
    markdown_text = re.sub(r"^(\++)\s*(.+)$", lambda match: "#" * len(match.group(1)) + " " + match.group(2), wiki_source, flags=re.MULTILINE)

    # Replace bold and italic text
    markdown_text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', markdown_text)
    markdown_text = re.sub(r'//(.*?)//', r'_\1_', markdown_text)

    # Replace anchors
    markdown_text = re.sub(r'anchor:\s*(\S+)', r'<a name="\1"></a>', markdown_text) # "anchor: something" -> '<a name="something"></a>
    markdown_text = re.sub(r'\[(.*?)\]\!(\S+)', r'[\1#\2]', markdown_text)      # [address]!anchor -> [address#anchor]

    # Replace links
    markdown_text = re.sub(r'\[([^#]*?)\|(.*?)\]', r'[\2](\1)', markdown_text) # [address|title] -> [address](title)
    markdown_text = re.sub(r'\[([^#]*?)\]',     r'[\1]',     markdown_text) # [address] -> [adress] - skip the above 

    # Replace bullet points
    markdown_text = re.sub(r'^(\*+)\s+(.*)$', r'\1 \2', markdown_text, flags=re.MULTILINE)

    # Replace ordered and unordered lists
    ##markdown_text = re.sub(r"^\s*\* (.+)$", r"* \1", markdown_text, flags=re.MULTILINE)
    ##markdown_text = re.sub(r"^\s*\d+\. (.+)$", r"1. \1", markdown_text, flags=re.MULTILINE)
    ##markdown_text = re.sub(r"^\s+[\*\d]", lambda match: " " * 4 + match.group(0), markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r"^(\s+)([\*\d])", lambda match: " " * (2 * len(match.group(1))//4 - 1) + match.group(2), markdown_text, flags=re.MULTILINE)

    # Replace horizontal lines
    markdown_text = re.sub(r'^----+$', r'---', markdown_text, flags=re.MULTILINE)

    # Replace tables
    markdown_text = re.sub(r"^(<<\|\s*|>>\s*)\n", r"", markdown_text, flags = re.MULTILINE) # table frame <<| and >>
    markdown_text = re.sub(r"^(.*\|.*\|.*)$", lambda match: "| " + " | ".join( elem.strip() for elem in match.group(0).split("|")) + " |", markdown_text, flags = re.MULTILINE) # cell delimiters: | elem1 | elem2 |
    if True:
        # this isn't necessary for 
        markdown_text = re.sub(r"(^\|.*\|\r?\n)+", table_add_header, markdown_text, flags = re.M) # add the colspec line to a line block


    # Remove any remaining WikidPad syntax
    if remove_remaining_wikidpad:
        markdown_text = re.sub(r'^\s*\*\s*\d+\s*', '', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'anchor:', '', markdown_text)
        markdown_text = re.sub(r'\[.*?\]', '', markdown_text)
    
    # Remove any remaining leading or trailing white space
    markdown_text = markdown_text.strip()

    # Replace any remaining carriage returns with line breaks
    markdown_text = markdown_text.replace('\r\n', '\n')

    return markdown_text

def WriteConfluencePage( space, title, parent_id = None, overwrite = True, body_markdown = ""):
    """Writes a confluence page

    Args:
        space (_type_): _description_
        title (_type_): _description_
        parent_id (_type_, optional): _description_. Defaults to None.
        overwrite (bool, optional): _description_. Defaults to True.
        body_markdown (str, optional): _description_. Defaults to "".

    Returns:
        str: URL to created page
    """
    assert _CONFLUENCE_CONNECTION
    pg = _CONFLUENCE_CONNECTION.get_page_by_title( space = space, title = title)

    representation = "wiki"
    body_source = body_markdown
    if ConfluenceRenderer and mistune:
        renderer = ConfluenceRenderer(use_xhtml=True)
        confluence_mistune = mistune.Markdown(renderer=renderer)
        body_source = confluence_mistune(body_markdown)
        representation = "storage"

    if pg and overwrite:
        data =  _CONFLUENCE_CONNECTION.update_existing_page( 
            page_id = pg["id"], 
            title = pg["title"], 
            representation = representation,
            body = body_source, 
        )
    else:
        data = _CONFLUENCE_CONNECTION.create_page( 
            space = space, 
            title = title, 
            parent_id = parent_id, 
            representation = representation, 
            body = body_source,
        )
    return data["_links"]["base"] + data["_links"]["webui"]

def RunMain( options = None,
             args    = None,
             **kwargs):
    u"""
    """
    
    if args is None:
        args = []

    # fetch and set parameters #
    options, args = ParseOptions(options, args, **kwargs)

    ####################
    # work starts here #
    ####################
    if not os.path.exists( options.output_dir):
        logging.info("--out dir '%s' not existing - creating", os.path.abspath( options.output_dir))
        os.mkdir( options.output_dir)

    wiki_files = glob.glob( options.wikidpad_files)
    logging.info("Found %s wikidpad files for %s", len( wiki_files), options.wikidpad_files)
    for _file in wiki_files:
        logging.debug("parsing %s", _file)

        with open( _file, "r", encoding = "utf8") as fh:
            wiki_content = fh.read()

        # transform wikidpad -> Markdown
        markdown_content = Wikidpad2Markdown( wiki_content, remove_remaining_wikidpad=False)

        # write out file
        fname = os.path.basename( _file)
        title = fname.rstrip(".wiki")
        target_path = os.path.join( options.output_dir, f"{title}.md")
        logging.debug("writing %s", target_path)
        with open( target_path, "w", encoding = "utf8") as fh_out:
            fh_out.write( markdown_content)
        logging.info("%s -> %s", _file, target_path)
        
        # verify
        if options.verify:
            verify_path = _file.rstrip(".wiki") + ".md"
            with open( verify_path, "r", encoding = "utf8") as fh_verify:
                verify_content = fh_verify.read().splitlines()
            if os.path.exists( verify_path):
                _diff = better_diff( 
                    left = verify_content, 
                    right = markdown_content.splitlines(), 
                    as_string=True, 
                    separator=" | ", 
                    skip_equal=True,
                    skip_whitespace_changes=True,
                    left_title= "verification (expected)", 
                    right_title="converted (obtained)")
                diff_count = len( _diff.splitlines())

                if _diff:
                    logging.warning("Conversion for %s differs from %s on %s lines", target_path, verify_path, diff_count)
                    print(_diff)
                    if options.Strict:
                        logging.error("Strict mode. Stopping after failed conversion / verification.")
                        sys.exit(EXIT_CRITICAL)
        # render to HTML
        if options.render:
            rendered_html = markdown.markdown( markdown_content)
            target_path_html = os.path.join( options.output_dir, f"{title}.html")
            with open( target_path_html, "w", encoding = "utf8") as html_out:
                html_out.write( rendered_html)
            logging.info("%s -> %s", _file, target_path_html)

        # write to confluence
        if options.ConfluenceURL:
            page_url = WriteConfluencePage( 
                space = options.ConfluenceSpace, 
                title = title, 
                parent_id = None, 
                overwrite = True, 
                body_markdown = markdown_content
            )
            logging.info( "Confluence Upload: %s -> %s", _file, page_url)
        
    logging.info("done.")

if __name__ == '__main__':
    if False:
        input("Connect to debugger?")
    loggingSetup( LOG_FILE)
    logging.info("== wikidpad to markdown transformer ==")
    logging.info("=" * 40)
    logging.info("Working in %s", os.getcwd())
    try:
        if False:
            RunMain( 
                verify = "_sample_pages",
                render  = True,
            )
        else:
            RunMain()
    except Exception as exc:
        logging.exception( "UNCAUGHT EXCEPTION")
        traceback.print_exc()
        sys.exit(EXIT_CRITICAL)