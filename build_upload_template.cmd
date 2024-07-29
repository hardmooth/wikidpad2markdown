:: run the wikidpad2markdown on your files.
:: 
:: this is an example/template, so you'll need to replace:
::  * WIKIDPAD_FOLDER
:: and for the confluence upload:
::  * YOUR_INSTANCE
::  * CONFLUENCE_TOKEN
::  * TARGET_ROOT_PAGE
::  * YOUR_CONFLUENCE_USER_MAIL
::  * CONFLUENCE_SPACE
python wikidpad2markdown.py --wikidpad=WIKIDPAD_FOLDER/data/*.wiki --out=out --confluence-url=https://YOUR_INSTANCE.atlassian.net/wiki --confluence-token=CONFLUENCE_TOKEN --confluence-parent-id=TARGET_ROOT_PAGE --confluence-user=YOUR_CONFLUENCE_USER_MAIL --confluence-space=CONFLUENCE_SPACE