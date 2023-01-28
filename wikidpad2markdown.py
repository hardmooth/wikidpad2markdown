# -*- coding: utf-8 -*-
"""
script to migrated from wikidpad to markdown (and possibly upload to confluence)
@copyright:   Hartmut Leister, 2023, all rights reserved
@author: Hartmut Leister <hartmut.leister@gmail.com>
"""

# -- python standard imports ---
import difflib
import glob
import logging
import os
import sys
import traceback
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

# -- local imports ---

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
    parser = OptionParser()
    parser.add_option("-w", "--wikidpad", dest="wikidpad_files", help="Input Wikidpad files (may be globular expression)")
    parser.add_option("-o", "--out",      dest="output_dir",    help="Output directory for generated Markdown files", default="out")

    parser.add_option("-V", "--verify", dest="verify", action="store", default=None, help="Verify created Markdown files against those in the given directly (for each'file.wiki' there must be 'file.md'")

    parser.add_option("--confluence-url", dest="ConfluenceURL", action="store", help = "Confluence upload: URL of confluence cloud instance")
    parser.add_option("--confluence-space", dest="ConfluenceSpace", action="store", help = "Confluence upload: Space Key")
    parser.add_option("--confluence-user", dest="ConfluenceUser", action="store", help = "Confluence upload: Name of user")
    parser.add_option("--confluence-parent-id", dest="ConfluenceParentID", action="store", help="Confluence upload: (optional) ID of parent page")
    parser.add_option("--confluence-token", dest="ConfluenceAPIToken", action="store", help = "Confluence upload: Confluence API Token")

    parser.add_option("-s", "--strict", dest="Strict", action="store_true", default=False, help="Abort on the first error (or keep going?).")

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
    if markdown is None:
        logging.warning( "'markdown' package is not installed. Generating HTML from markdown will fail ")

    if any( [options.ConfluenceURL, options.ConfluenceSpace, options.ConfluenceUser, options.ConfluenceAPIToken, ]):
        _CONFLUENCE_CONNECTION = confluence.Confluence(
            url=options.ConfluenceURL,
            username=options.ConfluenceUser,
            password=options.ConfluenceAPIToken,
            cloud=True
        )


    return options, args

def Wikidpad2Markdown( wiki_source):
    return wiki_source

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

    if pg and overwrite:
        data =  _CONFLUENCE_CONNECTION.update_existing_page( 
            page_id = pg["id"], 
            title = pg["title"], 
            representation = "wiki",
            body = body_markdown, 
        )
    else:
        data = _CONFLUENCE_CONNECTION.create_page( 
            space = space, 
            title = title, 
            parent_id = parent_id, 
            representation = "wiki", 
            body = body_markdown,
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

        markdown_content = Wikidpad2Markdown( wiki_content)

        fname = os.path.basename( _file)
        title = fname.rstrip(".wiki")
        target_path = os.path.join( options.output_dir, f"{title}.md")
        logging.debug("writing %s", target_path)
        with open( target_path, "w", encoding = "utf8") as fh_out:
            fh_out.write( markdown_content)
        logging.info("%s -> %s", _file, target_path)
        
        if options.verify:
            verify_path = _file.rstrip(".wiki") + ".md"
            with open( verify_path, "r", encoding = "utf8") as fh_verify:
                verify_content = fh_verify.readlines()
            if os.path.exists( verify_path):
                _diff = list(difflib.unified_diff( a = markdown_content.splitlines(), b = verify_content, fromfile = target_path, tofile = verify_path))
                diff_count = len([ diff_line for diff_line in _diff if diff_line.startswith("+") or diff_line.startswith("-")])
                if _diff:
                    logging.warning("Conversion for %s differs from %s on %s lines", target_path, verify_path, diff_count)
                    logging.warning("\n".join( line.rstrip() for line in _diff))
                    if options.Strict:
                        logging.error("Strict mode. Stopping after failed conversion / verification.")
                        sys.exit(EXIT_CRITICAL)
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
        RunMain()
    except Exception as exc:
        logging.exception( "UNCAUGHT EXCEPTION")
        traceback.print_exc()
        sys.exit(EXIT_CRITICAL)