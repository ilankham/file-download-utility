# This script requires a file named "config.py" in the same directory to define
# the following constants:
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

import logging
import pathlib
import shutil
import sys
import time
import zipfile

import requests


# record script start time to use in calculating a total script execution time
script_start_time = time.perf_counter()

# attempt to import config module from current directory
try:
    import config
except ModuleNotFoundError as e:
    raise FileNotFoundError(
        'A file named config.py must exist in the current directory'
    ) from e

# create log directory specified in config module, if needed
log_directory = pathlib.Path(config.LOG_DIRECTORY)
try:
    log_directory.mkdir(parents=True, exist_ok=True)
except FileExistsError as e:
    raise NotADirectoryError(
        f'{log_directory.absolute()} must be a directory or not yet exist'
    ) from e

# set logfile location using directory specified in config file
log_file_location = log_directory / config.LOG_FILE_NAME
log_handler = logging.FileHandler(log_file_location.absolute(), mode='a')

# create secondary logger to console output
screen_handler = logging.StreamHandler(stream=sys.stdout)

# set log format for both logfile and console output
log_formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d-%H:%M:%S',
)
log_handler.setFormatter(log_formatter)
screen_handler.setFormatter(log_formatter)

# create logger to simultaneously write to both logfile and console output
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)
logger.addHandler(screen_handler)

# test that logging system was successfully created
try:
    logger.info('Logging initiated')
except Exception as e:
    raise NotImplementedError(
        f'Logging could not be initiated'
    ) from e

# create download archive directory specified in config module
download_directory = pathlib.Path(config.DOWNLOAD_ARCHIVE_DIRECTORY)
logger.info(f'Download archive path is {download_directory.absolute()}')
try:
    download_directory.mkdir(parents=True, exist_ok=True)
except FileExistsError as e:
    m = f'{download_directory.absolute()} must be a directory or not yet exist'
    logger.exception(m)
    raise NotADirectoryError(m) from e

# create login session specified in config module
login_session = requests.Session()
logger.info(f'Now attempting to log into {config.BASE_URL}')
try:
    login_response = login_session.post(
        config.BASE_URL + config.LOGIN_PATH,
        data=config.LOGIN_HEADERS
    )
    logger.debug(f'HTTP headers: {login_response.headers}')
    login_response.raise_for_status()
except requests.exceptions.RequestException as e:
    m = 'unable to establish network connection'
    logger.exception(m)
    raise requests.exceptions.ConnectionError(m) from e

# iterate through all values in download actions dict; each download action
# value is also iterate over until a successful download is obtained
for k, v_list in config.DOWNLOAD_ACTIONS.items():
    if not isinstance(v_list, list):
        v_list = [v_list]
    for v in v_list:
        logger.info(
            f'Now attempting download "{k}" using method {v["method"]} and'
            f' metadata {v["metadata"]}'
        )
        logger.debug(f'Full download instructions: {v}')
        if v['method'].upper().strip() == 'POST':
            download_response = login_session.post(
                v['URL'],
                data=v['metadata'],
                stream=True
            )
        elif v['method'].upper().strip() == 'GET':
            download_response = login_session.get(
                v['URL'],
                params=v['metadata'],
                stream=True
            )
        else:
            m = f'Download "{v}" method {v["method"]} is unsupported'
            logger.exception(m)
            raise ValueError(m)
        if download_response.status_code == requests.codes.ok:
            logger.info(f'Download "{k}" was successful started')
            download_destination = download_directory / v['filename']
            try:
                with open(download_destination, 'wb') as fp:
                    download_response.raw.decode_content = True
                    shutil.copyfileobj(download_response.raw, fp)
                    logger.info(f'Download "{k}" was successful completed')
                    break
            except (requests.exceptions.ConnectionError, IOError) as e:
                    logger.exception(f'Download "{k}" was unsuccessful')

        else:
            logger.warning(
                f'Download "{k}" using method {v["method"]} and metadata'
                f' {v["metadata"]} could *NOT* be started'
            )
    else:
        logger.error(f'*** NO ITERATION OF DOWNLOAD "{k}" WAS SUCCESSFUL ***')

    if v['extract_zip'] and zipfile.is_zipfile(download_destination):
        logger.info(
            f'Now attempting to extract file {v["zip_member_to_extract"]}'
            f' from download "{k}" using zip decompression'
        )
        zip_file_contents_directory = (
            download_directory / v['filename'].split('.')[0]
        )
        try:
            with zipfile.ZipFile(str(download_destination.absolute())) as zfp:
                zfp.extract(
                    v['zip_member_to_extract'],
                    zip_file_contents_directory,
                )
                logger.info(
                    f'{v["zip_member_to_extract"]} was successfully extracted'
                    f' from download "{k}" using zip decompression'
                )
        except (zipfile.BadZipFile, IOError) as e:
            logger.exception(
                f'{v["zip_member_to_extract"]} was *not* successfully'
                f' extracted from download "{k}" using zip decompression'
            )
        final_destination = pathlib.Path(v['zip_member_final_destination'])
        if final_destination.exists():
            logger.warning(
                f'final destination {final_destination} for file'
                f'{v["zip_member_to_extract"]} already exists'
            )
        else:
            logger.info(
                f'final destination {final_destination} for file'
                f'{v["zip_member_to_extract"]} does not yet exist'
            )
        try:
            shutil.copy2(
                str(zip_file_contents_directory / v['zip_member_to_extract']),
                str(final_destination),
            )
            logger.info(
                f'file {v["zip_member_to_extract"]} successfully copied to'
                f' {final_destination}'
            )
        except IOError as e:
            logger.exception(
                f'file {v["zip_member_to_extract"]} could *not* be copied to'
                f' {final_destination}'
            )
    elif v['extract_zip']:
        logger.error(f'Download "{k}" is not a valid zip file')

logger.info(
    f'Total script execution time:'
    f' {time.perf_counter() - script_start_time:.02f} seconds'
)
