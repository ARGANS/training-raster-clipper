import logging
from pprint import pformat


def log_info(
    object,
    /,
    variable_name=None,
):
    if variable_name:
        if type(object) == str:
            logging.info(f"{variable_name}:\n{object}")
        else:
            logging.info(f"{variable_name}:\n{pformat(object)}")
    else:
        if type(object) == str:
            logging.info(object)
        else:
            logging.info(pformat(object))
