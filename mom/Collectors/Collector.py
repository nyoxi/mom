# Memory Overcommitment Manager
# Copyright (C) 2010 Adam Litke, IBM Corporation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import re
import sys
import logging

class Collector:
    """
    Collectors are plugins that return a specific set of data items pertinent to
    a given Monitor object every time their collect() method is called.  Context
    is given by the Monitor properties that are used to init the Collector.
    """
    def __init__(self, properties):
        """
        The Collector constructor should use the passed-in properties to
        establish context from its owning Monitor.
        Override this method when creating new collectors.
        """
        pass

    def collect(self):
        """
        The principle interface for every Collector.  This method is called by a
        monitor to initiate data collection.
        Override this method when creating new collectors.
        Return: A dictionary of statistics.
        """
        return {}

    def getFields(self):
        """
        Used to query the names of mandatory statistics fields that this
        Collector will return.
        A failure to collect mandatory fields must break the current cycle
        as the policy expects all fields to return.
        Collector authors should be aware that new collectors must guarantee
        the fields to be reported otherwise they must use optional fields.
        @see #getOptionalFields
        Override this method when creating new collectors.
        Return: A set containing the names of all statistics returned by collect()
        """
        return set()

    def getOptionalFields(self):
        """
        Used to query the names of optional statistics fields that this
        Collector will return.
        Override this method when creating new collectors.
        Return: A set containing the names of all statistics returned by collect()
        """
        return set()

def get_collectors(config_str, properties, global_config):
    """
    Initialize a set of new Collector instances for a Monitor.
    Return: A list of initialized Collectors
    """
    logger = logging.getLogger('mom.Collector')
    collectors = []

    # Make sure we don't clobber an existing entry in the properties dict
    if 'config' in properties:
        logger.error("Internal Error: 'config' not allowed in Monitor properties")
        return None

    for name in config_str.split(','):
        name = name.lstrip()
        if name == '':
            continue

        # Check for Collector-specific configuration in the global config
        section = "Collector: %s" % name
        if global_config.has_section(section):
            properties['config'] = dict(global_config.items(section, raw=True))

        # Create an instance
        try:
            module = __import__('mom.Collectors.' + name, None, None, name)
            collectors.append(getattr(module, name)(properties))
        except ImportError:
            logger.warning("Unable to import collector: %s", name)
            return None
        except FatalError as e:
            logger.error("Fatal Collector error: %s", e.msg)
            return None
    return collectors

#
# Collector Exceptions
#
class CollectionError(Exception):
    """
    This exception should be raised if a Collector has a problem during its
    collect() operation and it cannot return a complete, coherent data set.
    """
    def __init__(self, msg):
        self.msg = msg

class FatalError(Exception):
    """
    This exception should be raised if a Collector has a permanent problem that
    will prevent it from initializing or collecting any data.
    """
    def __init__(self, msg):
        self.msg = msg

#
# Collector utility functions
#
def open_datafile(filename):
    """
    Open a data file for reading.
    """
    try:
        filevar = open(filename, 'r')
    except IOError as e:
        logger = logging.getLogger('mom.Collector')
        logger.error("Cannot open %s: %s" % (filename, e.strerror))
        sys.exit(1)
    return filevar

def parse_int(regex, src):
    """
    Parse a body of text according to the provided regular expression and return
    the first match as an integer.
    """
    m = re.search(regex, src, re.M)
    if m:
        return int(m.group(1))
    else:
        return None

def count_occurrences(regex, src):
    """
    Parse a body of text according to the provided regular expression and return
    the count of matches as an integer.
    """
    m = re.findall(regex, src, re.M)
    if m:
        return len(m)
    else:
        return None
