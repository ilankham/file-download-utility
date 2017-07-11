# This script provides the following constants:
# - LOG_DIRECTORY, a string giving the directory for storing log files
# - LOG_FILE_NAME, a string giving a filename opened in config.LOG_DIRECTORY
# in append mode
# - DOWNLOAD_ARCHIVE_DIRECTORY, a string giving the directory for saving
# downloaded
# - BASE_URL, a string giving the base URL for a login action
# - LOGIN_PATH, a string giving the path to a login action
# - LOGIN_HEADERS, a dictionary giving the form data for a login action using
# a post method
# - DOWNLOAD_ACTIONS, a dictionary specifying download actions to attempt,
# with each value a dict or a list of dictionaries; if a value is a list of
# dictionaries, then each list item will be attempted until either a successful
# download is achieved or the list is exhausted; each dictionary should have
# the following keys:
# -- URL, with value a string comprising a full file-download URL
# -- method, with a string equal to either 'get' or 'post'
# -- metadata, with value a dictionary to be used either for post method form
# data or get method params, based on the method being used
# -- filename, with value a string comprising the filename after download
# -- extract_zip, with value a Boolean equivalent to either True or False
# -- zip_member_to_extract, with value a string comprising the file to extract
# from the downloaded file to a subdirectory of same name as zip file
# -- zip_member_final_destination, with value a string giving the final location
# to which the zip file member should be copied after extraction

from collections import OrderedDict
from datetime import datetime
from pprint import pprint


# create timestamp for creation of unique directory and file names
_current_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

# specify location and name for log files
LOG_DIRECTORY = './.script-logs'
LOG_FILE_NAME = f'script_log-{_current_timestamp}.log'

# specify location to store an archive of all downloaded files
DOWNLOAD_ARCHIVE_DIRECTORY = './.download_archive'

# set parameters for logging in
BASE_URL = 'http://httpbin.org/'
LOGIN_PATH = 'post'
LOGIN_HEADERS = {
    'custname':'test_username',
    'custemail':'test_email'
}
# create ordered dict of download actions
DOWNLOAD_ACTIONS = OrderedDict()

image_types = ['png','jpeg','webp','svg']
for image_type in image_types:
    DOWNLOAD_ACTIONS[image_type] = {
        'URL':f'{BASE_URL}image/{image_type}',
        'method':'get',
        'metadata':{},
        'filename':
            f'httpbin_example_image-downloaded_'
            f'{_current_timestamp}.{image_type}',
        'extract_zip':False,
        'zip_member_to_extract':None,
        'zip_member_final_destination':None,
    }


if __name__ == '__main__':
    pprint(DOWNLOAD_ACTIONS)
