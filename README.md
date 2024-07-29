# wikidpad2markdown

Transforms wikidpad pages to markdown syntax. Optionally uploads as separate pages to Confluence (cloud).

[wikidPad](https://wikidpad.sourceforge.net/) is an open source wiki-like notebook. 
As it is not actively developed since 2018 this script helps to migrate to other wiki tools (i.e. Confluence) using [Markdown](https://markdown.de/)

## Notes

 * still a 90% solution - tested on production and translates most of the stuff, yet not everything (no full syntax, no page tree structure, no linked pages)
 * Will escape HTML characters and entities in markdown (or will break confluence)
 * Will replace "%2F" by "/" in filenames when uploading to confluence (those are escaped "/" anyway)

## Setup

 1. install python (tested with 3.10)
 1. clone this repository and point to your files (and optionally confluence instance)
 1. install python requirements
    
        pip install -r requirements.txt
 1. point to your files (and confluence instance) by copying and editing `build_upload_template.cmd`

## Usage

To transform your wikidpad pages to markdown, run it like:

    python wikidpad2markdown.py --wikidpad=<path_to_pages>/*.wiki --out=<markdown_out>

to also upload the generated page to confluence use it like (insert your data):

    python wikidpad2markdown.py --wikidpad=_sample_pages/*.wiki --out=out --strict --confluence-url=https://<your_atlassian_instance>.atlassian.net/wiki --confluence-token=<your_confluence_cloud_API_token> --confluence-parent-id=<optional_confluence_parent_page_id> --confluence-user=<your_atlassian_user_email> --confluence-space=<target_space_key>

You can store the above line in a `build_custom.cmd`, which is already ignored.<br>
An example file `build_upload_template.cmd` is supplied.

other options are:

    Usage: wikidpad2markdown.py [options]
    
    Options:
      -h, --help            show this help message and exit
      -w WIKIDPAD_FILES, --wikidpad=WIKIDPAD_FILES
                            Input Wikidpad files (may be globular expression)
      -o OUTPUT_DIR, --out=OUTPUT_DIR
                            Output directory for generated Markdown files
      -u, --update          Should already existing/processed files be
                            updated/overwritten (default: skip)
      -V VERIFY, --verify=VERIFY
                            Verify created Markdown files against those in the
                            given directly (for each'file.wiki' there must be
                            'file.md'
      -R, --render          Render transformed files to HTML as well.
      --confluence-url=CONFLUENCEURL
                            Confluence upload: URL of confluence cloud instance
      --confluence-space=CONFLUENCESPACE
                            Confluence upload: Space Key
      --confluence-user=CONFLUENCEUSER
                            Confluence upload: Name of user
      --confluence-parent-id=CONFLUENCEPARENTID
                            Confluence upload: (optional) ID of parent page
      --confluence-token=CONFLUENCEAPITOKEN
                            Confluence upload: Confluence API Token
      -s, --strict          Abort on the first error (or keep going?).
  
## Tests

Unit Tests are done using [Pytest](https://docs.pytest.org/).

### Running Tests

Tests are (not yet) run automatically, but can be run manually via::
    
    pytest

### Writing Tests

Simply add other pytest tests in `tests/` as of the [Pytest docs](https://docs.pytest.org/).
