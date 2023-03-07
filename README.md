# wikidpad2markdown
Transforms wikidpad pages to markdown syntax. Also planned to upload pages to confluence cloud.

[wikidPad](https://wikidpad.sourceforge.net/) is an open source wiki-like notebook. 
As it is not actively developed since 2018 this script helps to migrate to other wiki tools (i.e. Confluence) using [Markdown](https://markdown.de/)

> :warning: **This project has just been started and has not been tested on real life wikis.**

## Usage

To transform your wikidpad pages to markdown, run it like:

    python wikidpad2markdown.py --wikidpad=<path_to_pages>/*.wiki --out=<markdown_out>

to also upload the generated page to confluence use it like (insert your data):

    python wikidpad2markdown.py --wikidpad=_sample_pages/*.wiki --out=out --strict --confluence-url=https://<your_atlassian_instance>.atlassian.net/wiki --confluence-token=<your_confluence_cloud_API_token> --confluence-parent-id=<optional_confluence_parent_page_id> --confluence-user=<your_atlassian_user_email> --confluence-space=<target_space_key>

You can store the above line in a `build_custom.cmd`, which is already ignored.

other options are:

        Options:
      -h, --help            show this help message and exit
      -w WIKIDPAD_FILES, --wikidpad=WIKIDPAD_FILES
                            Input Wikidpad files (may be globular expression)
      -o OUTPUT_DIR, --out=OUTPUT_DIR
                            Output directory for generated Markdown files
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

