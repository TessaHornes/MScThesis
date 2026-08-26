import os
import sys
import numpy as np

# Make GeoDFN importable from the cloned repo at the project root
_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GEODFN_ROOT = os.path.join(_HERE, 'GeoDFN')
if _GEODFN_ROOT not in sys.path:
    sys.path.insert(0, _GEODFN_ROOT)

from GeoDFN import DFNGenerator, DFNGeneratorWithSeed, DFNGeneratorWithSeedAndExclusion


def realizations_to_frac_array(realizations):
    """
    Convert GeoDFN realizations list to a list of (frac_data, apertures) tuples.

    Each realization is a list of fracture sets; each set is a list of fracture
    dicts with keys x_start, y_start, x_end, y_end, fracture aperture.

    Returns
    -------
    list of (ndarray shape (N,4), ndarray shape (N,)) pairs — one per realization.
    """
    result = []
    for realization in realizations:
        all_fracs = [frac for frac_set in realization for frac in frac_set]
        frac_data = np.array(
            [[f['x_start'], f['y_start'], f['x_end'], f['y_end']] for f in all_fracs]
        )
        apertures = np.array([f['fracture aperture'] for f in all_fracs])
        result.append((frac_data, apertures))
    return result


def save_dfns_as_text(realizations, dfn_name, base_dir='DFNs'):
    """
    Save GeoDFN realizations as the plain-text files expected by this project.

    Files are written to  <base_dir>/<dfn_name>/Text/DFN001.txt, DFN002.txt, ...
    Each file has one fracture segment per line: x1 y1 x2 y2

    Returns
    -------
    list of str — absolute paths to the written files.
    """
    text_dir = os.path.join(base_dir, dfn_name, 'Text')
    os.makedirs(text_dir, exist_ok=True)

    paths = []
    for i, realization in enumerate(realizations):
        all_fracs = [frac for frac_set in realization for frac in frac_set]
        frac_data = np.array(
            [[f['x_start'], f['y_start'], f['x_end'], f['y_end']] for f in all_fracs]
        )
        filepath = os.path.join(text_dir, f'DFN{i + 1:03d}.txt')
        np.savetxt(filepath, frac_data, fmt='%.4f')
        paths.append(filepath)
        print(f'  Written {filepath}  ({frac_data.shape[0]} fractures)')

    return paths


def generate_and_save(dfn_name, domainLengthX, domainLengthY, sets,
                      apertureCalculationParameters, numOfRealizations=1,
                      base_dir='DFNs', generator_class=DFNGenerator, **kwargs):
    """
    Run GeoDFN and save the results in the Text directory used by this project.

    Parameters
    ----------
    dfn_name : str
        Name of the DFN campaign (used as subdirectory and DFNName inside GeoDFN).
    domainLengthX, domainLengthY : float
        Domain dimensions in metres.
    sets : list of dict
        Fracture-set configurations accepted by GeoDFN.
    apertureCalculationParameters : dict
        Aperture model parameters accepted by GeoDFN.
    numOfRealizations : int
        Number of stochastic realisations to generate.
    base_dir : str
        Root output directory (default 'DFNs').
    generator_class : class
        Which GeoDFN generator class to use (DFNGenerator, DFNGeneratorWithSeed,
        or DFNGeneratorWithSeedAndExclusion).
    **kwargs
        Any extra keyword arguments forwarded to the generator class constructor.

    Returns
    -------
    list of str — paths to the written DFN text files.
    """
    print(f'Generating {numOfRealizations} DFN realization(s) with GeoDFN ...')
    gen = generator_class(
        domainLengthX=domainLengthX,
        domainLengthY=domainLengthY,
        sets=sets,
        apertureCalculationParameters=apertureCalculationParameters,
        DFNName=dfn_name,
        numOfRealizations=numOfRealizations,
        output_dir=base_dir,
        **kwargs,
    )
    print('Generation complete.')
    return save_dfns_as_text(gen.realizations, dfn_name, base_dir=base_dir)
