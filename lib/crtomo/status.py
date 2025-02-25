"""

"""
import os
import re
import glob


def is_tomodir(directory):
    """Check if the supplied directory is a tomodir

    Parameters
    ----------
    directory: string
        Check if the supplied path is a valid tomodir

    Returns
    -------
    is_tomodir: bool
        True if the supplied directory is a tomodir directory
    """
    if os.path.isdir(directory):
        if(os.path.isdir(directory + "/exe") and
           os.path.isdir(directory + "/config") and
           os.path.isdir(directory + "/rho") and
           os.path.isdir(directory + "/inv") and
           os.path.isdir(directory + "/mod")):
                return True
        else:
                return False
    else:
        return False


def td_is_finished(tomodir):
    """Return the state of modeling and inversion for a given tomodir. The
    result does not take into account sensitivities or potentials, as
    optionally generated by CRMod.

    Parameters
    ----------
    tomodir: string
        Directory to check

    Returns
    -------
    crmod_is_finished: bool
        True if a successful CRMod result is contained in the tomodir
        directory.
    crtomo_is_finished: bool
        True if a successful CRTomo inversion results is contained in the
        tomodir directory.
    """
    if not is_tomodir(tomodir):
        raise Exception('Supplied directory is not a tomodir!')

    # crmod finished is determined by:
    # config.dat/rho.dat/crmod.cfg are present
    # volt.dat is present
    if(os.path.isfile(tomodir + os.sep + 'config/config.dat') and
       os.path.isfile(tomodir + os.sep + 'rho/rho.dat') and
       os.path.isfile(tomodir + os.sep + 'grid/elem.dat') and
       os.path.isfile(tomodir + os.sep + 'grid/elec.dat') and
       os.path.isfile(tomodir + os.sep + 'exe/crmod.cfg') and
       os.path.isfile(tomodir + os.sep + 'mod/volt.dat')):
        crmod_is_finished = True
    else:
        crmod_is_finished = False

    # crtomo is finished if
    # crtomo.cfg/volt.dat/elem.dat/elec.dat are present
    # inv/run.ctr contains the word "CPU" in the last line
    if(os.path.isfile(tomodir + os.sep + 'grid/elem.dat') and
       os.path.isfile(tomodir + os.sep + 'grid/elec.dat') and
       os.path.isfile(tomodir + os.sep + 'exe/crtomo.cfg') and
       os.path.isfile(tomodir + os.sep + 'inv/inv.ctr') and
       os.path.isfile(tomodir + os.sep + 'inv/run.ctr') and
       os.path.isfile(tomodir + os.sep + 'mod/volt.dat')):
        with open(tomodir + os.sep + 'inv/run.ctr', 'r') as fid:
            lines = fid.readlines()
            crtomo_is_finished = False
            # check the last 5 lines
            for line in lines[-5:]:
                test_line = line.strip()
                regex = re.compile('CPU')
                result = regex.match(test_line)
                if result is not None:
                    crtomo_is_finished = True
    else:
        crtomo_is_finished = False
    return crmod_is_finished, crtomo_is_finished


def is_sipdir(directory):
    """ Simple check if the supplied directory is a SIP directory.

    Parameters
    ----------
    directory: string
        Check if the supplied path is a valid SIP directory


    Returns
    -------
    is_sipdir: bool
        True if the supplied directory is a SIP directory
    """
    is_sipdir = True

    if(not os.path.isfile(directory + os.sep + 'frequencies.dat')):
        is_sipdir = False

    if(not os.path.isdir(directory + os.sep + 'invmod')):
        is_sipdir = False

    return is_sipdir


def sipdir_is_finished(sipdir):
    """Return the state of modeling and inversion for a given SIP dir. The
    result does not take into account sensitivities or potentials, as
    optionally generated by CRMod.

    Parameters
    ----------
    sipdir: string
        Directory to check

    Returns
    -------
    crmod_is_finished: bool
        True if all tomodirs of this SIP directory contain finished modeling
        results.
    crtomo_is_finished: bool
        True if all tomodirs of this SIP directory contain finished inversion
        results.

    """
    if not is_sipdir(sipdir):
        raise Exception('Directory is not a valid SIP directory!')

    subdirs_raw = sorted(glob.glob(sipdir + os.sep + 'invmod' + os.sep + '*'))
    subdirs = [x for x in subdirs_raw if os.path.isdir(x)]

    crmod_finished = True
    crtomo_finished = True
    for subdir in subdirs:
        subcrmod, subcrtomo = td_is_finished(subdir)
        if not subcrmod:
            crmod_finished = False
        if not subcrtomo:
            crtomo_finished = False

    return crmod_finished, crtomo_finished
