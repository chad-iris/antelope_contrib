'''
export_events.functions

Some functions used by event2qml main code
'''
# pylint:disable=logging-not-lazy,broad-except
from __future__ import print_function

import math
import logging

try:
    from antelope import stock
    from antelope import datascope
except ImportError as ex:
    print('Do you have Antelope installed correctly?')
    print(ex)


def simple_table_present(table, dbpointer):
    '''
    Verify if we have a table before we run the command.

    Similar to verify_table but without rising exceptions
    and without returning any objects back. It will only work
    out a dbpointer and not a database name. The pointer
    should be verified already.
    '''

    logger = logging.getLogger(__name__)

    try:
        view = dbpointer.lookup(table=table)
    except Exception as ex:
        logger.warning(
            'Exception while checking for presence of table %s: %s'
            % (table, ex))
        return False

    return view.query(datascope.dbTABLE_PRESENT)


def verify_table(table, database=None, dbpointer=None):
    '''
    Open a database or database pointer and verify existence of a table.

    On multiple objects (classes) we perform the same process
    of verifying the presence of a table before we get to
    interact with it. This will make that process easy since
    you can get to that point either from a database name
    or from a database pointer. The function will return
    the database pointer that you are responsible for
    cleaning later. The local view of the table will be
    freed.
    '''
    logger = logging.getLogger(__name__)
    assert database is not None or dbpointer is not None

    if database is not None:
        dbpointer = datascope.dbopen(database, "r")

    # Test if we have some table first.
    view = dbpointer.lookup(table=table)

    if not view.query(datascope.dbTABLE_PRESENT):
        logger.debug('Table [%s] not in database' % table)
        return None
    else:
        logger.debug('Table [%s] present in database' % table)

    return dbpointer


def is_null(value, null_value):
    '''
    Verify if our value matches the NULL
    representation of that field.
    '''
    # try numeric equality
    try:
        if int(float(value)) == int(float(null_value)):
            return True
    except ValueError:
        # try string equality
        return str(value) == str(null_value)


def get_all_fields(dbpointer, nulls=None):
    '''
    At a given database pointer to a particular record query for valid
    table fields and pull all values. Return a dictionary with the values.
    '''
    results = {}
    # logger = logging.getLogger(__name__)

    if not dbpointer or not dbpointer.query(datascope.dbTABLE_PRESENT):
        return results

    for index in range(dbpointer.query(datascope.dbFIELD_COUNT)):

        dbpointer.field = index

        table = dbpointer.query(datascope.dbFIELD_BASE_TABLE)
        field = dbpointer.query(datascope.dbFIELD_NAME)

        table_field = "%s.%s" % (table, field)
        value = dbpointer.getv(table_field)[0]

        if nulls is not None and table_field in nulls:
            if is_null(value, nulls[table_field]):
                # logger.debug('Skipping null "%s" in "%s"'
                #              % (value, table_field))
                continue

        results[table_field] = value

    return results


def open_verify_pf(pf, mttime=False):
    '''
    Verify that we can get the file and check
    the value of PF_MTTIME if needed.
    Returns pf_object
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Look for parameter file: %s' % pf)

    if mttime:
        logger.debug('Verify that %s is newer than %s' % (pf, mttime))

        pf_status = stock.pfrequire(pf, mttime)
        if pf_status == stock.PF_MTIME_NOT_FOUND:
            logger.warning('Problems looking for %s.' % pf +
                           ' PF_MTTIME_NOT_FOUND.')
            logger.error('No MTTIME in PF file. '
                         'Need a new version of the %s file!!!' % pf)
        elif pf_status == stock.PF_MTIME_OLD:
            logger.warning('Problems looking for %s. PF_MTTIME_OLD.' % pf)
            logger.error('Need a new version of the %s file!!!' % pf)
        elif pf_status == stock.PF_SYNTAX_ERROR:
            logger.warning('Problems looking for %s. PF_SYNTAX_ERROR.' % pf)
            logger.error('Need a working version of the %s file!!!' % pf)
        elif pf_status == stock.PF_NOT_FOUND:
            logger.warning('Problems looking for %s. PF_NOT_FOUND.' % pf)
            logger.error('No file  %s found!!!' % pf)

        logger.debug('%s => PF_MTIME_OK' % pf)

    try:
        return stock.pfread(pf)
    except Exception as ex:
        logger.error('Problem looking for %s => %s' % (pf, ex))


def safe_pf_get(pf, field, defaultval=False):
    '''
    Safe method to extract values from parameter file
    with a default value option.
    '''
    logger = logging.getLogger(__name__)
    value = defaultval
    if pf.has_key(field):  # noqa
        try:
            value = pf.get(field, defaultval)
        except Exception as ex:
            logger.warning('Problem with safe_pf_get(%s, %s)' % (field, ex))

    logger.debug("pf.get(%s,%s) => %s" % (field, defaultval, value))

    return value


# def _str(item):
#    '''Return a string no matter what'''
#    if item is not None:
#        return str(item)
#    else:
#        return ''
#

# def _dict(*args, **kwargs):
#    '''
#    Return a dict only if at least one value is not None
#    '''
#    dict_ = Dict(*args, **kwargs)
#    if dict_.values() == [None] * len(dict_):
#        return None
#    return dict_


def filter_none(obj):
    '''
    Return a dict only if the value for key "value" is not None.
    '''
    if obj.get('value') is None:
        return None
    return obj


def km2m(distance_km):
    '''Convert distance_km to meters only if not None.'''
    if distance_km is None:
        return None
    else:
        return float(distance_km) * 1000.


EARTH_MEAN_MERIDIONAL_RADIUS_M = 6367449.
M_PER_DEGREE_LATITUDE = math.pi*EARTH_MEAN_MERIDIONAL_RADIUS_M/180.
EARTH_MEAN_EQUATORIAL_RADIUS_M = 6378137.
M_PER_DEGREE_LONGITUDE = math.pi*EARTH_MEAN_EQUATORIAL_RADIUS_M/180.


def m2deg_lat(distance_m):
    '''Convert distance_m to degrees latitude only if not None.'''
    if distance_m is None:
        return None
    else:
        return float(distance_m) / M_PER_DEGREE_LATITUDE


def m2deg_lon(distance_m, latitude=0.0):
    '''Convert distance_m to degrees longitude only if not None.'''
    if distance_m is None:
        return None
    else:
        return (float(distance_m) / M_PER_DEGREE_LONGITUDE /
                math.cos(math.radians(latitude)))


def _eval_ellipse(smajax, sminax, angle):
    return smajax*sminax/(math.sqrt((sminax*math.cos(math.radians(angle)))**2 +
                                    (smajax*math.sin(math.radians(angle)))**2))


def get_ne_on_ellipse(smajax, sminax, strike):
    '''
    Return the solution for points north and east on an ellipse

    Arguments
    ---------
    smajax: float
        semi-major axis
    sminax: float
        semi-minor axis
    strike: float
        orientation of major axis, angle measured from north

    Returns
    -------
    2-tuple of floats:
        north, east
    '''
    north = _eval_ellipse(smajax, sminax, strike)
    east = _eval_ellipse(smajax, sminax, strike-90)
    return north, east


if __name__ == "__main__":
    raise ImportError("\n\n\tAntelope's qml module. Do not run directly! **\n")
