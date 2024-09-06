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
    `aws s3 cp --no-sign-request --recursive s3://elevation-tiles-prod/skadi ./data/mapzen`
* To convert it from the hgt files it comes as to the geotiff files I read  
  - Install GDAL
    `sudo apt install gdal-bin`
  - deflate:
    `python ../bin/mapzen_hgt_to_geotiff --remove`
    - That is a wrapper around:
      `gdal_translate -co COMPRESS=DEFLATE -co PREDICTOR=2 {hgt_filename} {tif_filename}`

Dependancies:
- `pip install geopy`
- `pip install geotiff`
- `pip install numpy-stl`


