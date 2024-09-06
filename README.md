# PyTerrainModeler

* Warning
  These instructions are known to work on my Ubuntu system.  It's a outline for getting this to work
  not a map or a guide. I am, after all, Unintelligible Maker.

* To get Map Data:
  - install awscli
    `sudo apt install awscli`
  - Make dir
    `mkdir MapZen`
    `cd MapZen`
  - fetch map data
    `aws s3 cp --no-sign-request --recursive s3://elevation-tiles-prod/skadi ./`
* To convert it from the hgt files it comes as to the geotiff files I read  
  - Install GDAL
    `sudo apt install gdal-bin`
  - deflate:
    `python ../bin/mapzen_hgt_to_geotiff --remove`
    - That is a wrapper around:
      `gdal_translate -co COMPRESS=DEFLATE -co PREDICTOR=2 {hgt_filename} {tif_filename}`

* Dependancies:
  - GeoPy
    `pip install geopy`
  - GeoTiff
    `pip install geotiff`
  - numpy-stl
    `pip install numpy-stl`


* Model Errors
  - If a model has a hole in it; meaning there are places of 0 (unitless but usually mm) z-height 
    that are left out.  It can create a "model" that is not totally connected and one objedt...but
    an STL has only one object.  So mine ends up somewhat deformed but eh.  Most slicers will be
    OK with this, though some will point out the model errors.  I ignore them but that's just me
    and I am, after all, Unintelligible Maker.