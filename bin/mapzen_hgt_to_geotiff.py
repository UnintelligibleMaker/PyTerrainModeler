#!/usr/bin/env python

"""mapzen_hgt_to_geotiff.py:
    This Python script converts MapZen HGT (Height) data files to the GeoTIFF format, which is a standard raster
    data format for geographic information systems (GIS). It allows you to specify the source folder containing
    the MapZen data and the destination folder for the converted GeoTIFF files (which can be the same), as well
    as an option to remove the original HGT files after conversion to save on disk space. As this is a one-time
    use script, to set up the data, and then never used again; I have not parallelized it in any way.  This also
    aids in you reading it and seeing exactly what I am asking your computer to do with the sys calls.  I ran it
    overnight.
    __author__      = "Unintelligible Maker"
    __copyright__   = "Copyright 2024"
    __license__     = "GNU GPL v3"
    __version__     = "1.0"
    __maintainer__  = "Unintelligible Maker"
    __email__       = "maker@unintelligiblemaker.com"
"""

from argparse import ArgumentParser
import logging
import os

LONGITUDE_FOLDERS = ["N00", "N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N09",
                     "N10", "N11", "N12", "N13", "N14", "N15", "N16", "N17", "N18", "N19",
                     "N20", "N21", "N22", "N23", "N24", "N25", "N26", "N27", "N28", "N29",
                     "N30", "N31", "N32", "N33", "N34", "N35", "N36", "N37", "N38", "N39",
                     "N40", "N41", "N42", "N43", "N44", "N45", "N46", "N47", "N48", "N49",
                     "N50", "N51", "N52", "N53", "N54", "N55", "N56", "N57", "N58", "N59",
                     "N60", "N61", "N62", "N63", "N64", "N65", "N66", "N67", "N68", "N69",
                     "N70", "N71", "N72", "N73", "N74", "N75", "N76", "N77", "N78", "N79",
                     "N80", "N81", "N82", "N83", "N84", "N85", "N86", "N87", "N88", "N89",
                     "N90", "S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09",
                     "S10", "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18", "S19",
                     "S20", "S21", "S22", "S23", "S24", "S25", "S26", "S27", "S28", "S29",
                     "S30", "S31", "S32", "S33", "S34", "S35", "S36", "S37", "S38", "S39",
                     "S40", "S41", "S42", "S43", "S44", "S45", "S46", "S47", "S48", "S49",
                     "S50", "S51", "S52", "S53", "S54", "S55", "S56", "S57", "S58", "S59",
                     "S60", "S61", "S62", "S63", "S64", "S65", "S66", "S67", "S68", "S69",
                     "S70", "S71", "S72", "S73", "S74", "S75", "S76", "S77", "S78", "S79",
                     "S80", "S81", "S82", "S83", "S84", "S85", "S86", "S87", "S88", "S89",
                     "S90"]

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-d", "--destination", help="Folder the GeoTiffs should be saved to. Default is ./")
    parser.add_argument("-s", "--source", help="Folder the MapZen data is in. This is the N00 - S90 folders. Default is ./")
    parser.add_argument("-r", "--remove", action="store_true", help="Indicates if the original *.hgt.gz files should be deleted as the script runs.")

    args = parser.parse_args()
    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logging.INFO)
    logging.debug(f"Args: {args}")

    if args.source is None:
        args.source = os.getcwd()
    else:
        args.source = os.path.abspath(args.source)

    if args.destination is None:
        args.destination = os.getcwd()
    else:
        args.destination = os.path.abspath(args.destination)

    logging.debug(f"Args: {args}")

    for longitude_folder in LONGITUDE_FOLDERS:
        longitude_folder_path = os.path.join(args.source, longitude_folder)
        for listing in os.listdir(longitude_folder_path):
            if listing.endswith(".hgt.gz"):
                hgt_gz_file = os.path.join(longitude_folder_path, listing)
                os.system(f"gunzip {hgt_gz_file}")
                hgt_file = hgt_gz_file.replace(".gz", "")
                tif_filename = os.path.join(args.destination, longitude_folder, listing.replace(".hgt.gz", ".tiff"))
                os.system(f"gdal_translate -co COMPRESS=DEFLATE -co PREDICTOR=2 {hgt_file} {tif_filename}")
                if args.remove:
                    os.remove(hgt_file)
                else:
                    os.system(f"gzip {hgt_file}")
