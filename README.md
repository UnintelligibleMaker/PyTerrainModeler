# PyTerrainModeler

* Warning
  These instructions are known to work on my Ubuntu system.  It's an outline for getting this to work
  not a map or a guide. I am, after all, Unintelligible Maker.

* To get Map Data:
  - install awscli
    - Older systems use:
      `sudo apt install awscli`
    - Newer ones use:
      `sudo snap install aws-cli --classic`
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

* Building an example model
  - Mount Rainier
    - Dry run/Draft: lower res/quicker.  I use this mode when changing other settings and tuning them to a good model
      `python ./bin/Rainier.py -n`
    - Full Quality.  This will take a while.  
      `python ./bin/Rainier.py`
  - Other Examples:
    - ./bin/King&Peirce.py
    - ./bin/Lake\ Washington.py
    - ./bin/Yosemite.py
    - ./bin/Italy.py
    - ./bin/Mauna\ Kea.py

* Building your own model - The Options
  - latitude: This is the latitude of the South West corner of the area to be modeled.  Float -90.0 - 90.0
  - longitude: This is the longitude of the South Westcorner of the area to be modeled.  Float -180.0 - 180.0
  - longitude_size: This is the size (length) of the south edge of the map in longitude. Float.
  - size_x: size of the model's x axis.  Technically unitless but usually mm.
  - size_y: size of the model's y axis.  Technically unitless but usually mm.
  - steps_x: number of steps in x direction.  This and the size_x determine the model's resolution in the x direction.
  - steps_y: number of steps in y direction.  This and the size_y determine the model's resolution in the x direction.
  - scale_z: factor by which to increase the scale in the z direction.  This is often needed on larger models to accentuate features that would other wise be flat.
  - offset_elevation: offset of the elevation in the map.  If you map is a long way above sea level or extends below sealevel you can use this to push the "0" elevation of sealevel up or down.  Note in the Yosemite.py example I set the offest to 1000m which is just below the valley floor.  This makes the bottom of the model thinner.  In the King&Peirce.py I use -400M to raise sealevel on the model and include the Puget Sound Shipping channel's depth.  Float in meters.
  - min_allowed_z: minimum allowed z.  forces z to be a minimum thickness. This does not move the model....it just fills in by moving any point lower then this to this level.  I've used this to model "what if" rises in sealevel.  Float in unitless (usually mm) on the model but the reality is this is an older option that I don't use much but don't see a reason to remove.
  - Flattening options.
    The flatening option serves dual purposes.  First it allows some "squishing" on the extreme highs and lows on the model towards a referance elevation.  This is useful especially if you model has flater areas you want to use scale_z on but also lower/higher areas that this makes too high.  This exponentially squishes the model to help remove that.  You can see this in the King&Peirce.py where I use 0.9 to make the mountians not so extra tall looking.  The other usage here is that in the small scale, within a meter of the referance elevation is pushed out towards the meter...further accentuationg features at this specific height.  So in the case of the King&Peirce.py I was trying to get Lake Washington and Mercer Island to look right...so by setting the referance height at the surface of the lake I make the outline clearer.  Note that I only flatten in the positive direction in that example to leave the shipping channel more dramatic looking.
    - flatten_reference_elevation_meters: flatten reference elevation in meters
    - flatten_factor: flatten factor to logrythmicly flatten by.  0.6 - 0.98 usually.
    - flatten_mode: flatten mode - Can be None, FlattenMode.POSITIVE (above the referance), FlattenMode.NEGATIVE (below the referance) or FlattenMode.BOTH.
  - geotiff_folder: geotiff folder The folder where the geotiffs are stored.  See above for how to get these.  The script will only open the ones needed so you can try to only have the ones you need.....but I just keep the whole cache on my drive.
  - xyz_config: xyz config = The XYZ Config for NOOA XYZ files.
                {surface elevation: [file, file, file, ... ],
                 surface elevation: [file, file, file, ... ]
                 ...}
  - max_processes: The maxiumim number of processes to have running at a time.  In most cases the default `os.cpu_count() * 2` is good.  Fair warning `1` is mostly for debug so it forces some things to not be parallelized but I do not recommend that unless you are debugging PyTerrainModeler itself.  For example I did a LOT or runs with steps_x & steps_y = 4 and this at one to get the trianges facing the right directions (in vs out).
  In general for me making a model is an iterative process.  I get the latitude, longitude, and longitude_size from any online mapping program (I use google maps but any will do).  The size_x and size_y are how big I want the model on the printer and I usually know.  I start with low steps_x and steps_y to keep the iteration time low.  The offset_elevation, scale_z, flatten_reference_elevation_meters, flatten_factor, and flatten_mode are the options I iterate on changing until the model looks right.  Then I set the steps_x and steps_y to get a detailed model.  
    
* Model Errors
  - If a model has a hole in it, meaning there are places of 0 (unitless but usually mm) z-height 
    that are left out, t can create a "model" that is not totally connected and one object...but
    an STL has only one object.  So mine ends up somewhat deformed but eh both Cura and PrusaSlicer open and slice them.
  - Sometimes (though it's rare now) a triangle faces the wrong way (in vs out of the model).  There are 
    bugs that I hope are getting rarer.  I'm good with righty-tighty / lefty-loosey even when rotated 
    backwards but not as good with clockwise and anti-clockwise when rotated backwards. 
    Most slicers will be OK with this, though some will point out the model errors.  I ignore them and let the slicers deal with it but that's 
    just me, and I am an Unintelligible Maker.
