# PyTerrainModeler

* Warning
  These instructions are known to work on my Ubuntu system.  It's an outline for getting this to work
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

* Dependencies:
  - GeoPy
    `pip install geopy`
  - GeoTiff
    `pip install geotiff`
  - numpy-stl
    `pip install numpy-stl`

* Building a model
  - Mount Rainier
    - Dry run/Draft: lower res/quicker.  I use this mode when changing other settings and tuning them to a good model
      `python ./bin/Rainier.py -n`
    - Full Quality.  THis will take a while.  
      `python ./bin/Rainier.py`
  - Other Examples:
    - ./bin/King&Peirce.py
    - ./bin/Lake\ Washington.py
    - ./bin/Yosemite.py
    
* Model Errors
  - If a model has a hole in it, meaning there are places of 0 (unitless but usually mm) z-height 
    that are left out, t can create a "model" that is not totally connected and one object...but
    an STL has only one object.  So mine ends up somewhat deformed but eh.  
  - Sometimes (though it's rare now) a triangle faces the wrong way (in vs out of the model).  There are 
    bugs that I hope are getting rarer.  I'm good with righty-tighty / lefty-loosey even when rotated 
    backwards but not as good with clockwise and anti-clockwise when rotated backwards. 
    Most slicers will be OK with this, though some will point out the model errors.  I ignore them but that's 
    just me, and I am an Unintelligible Maker.
