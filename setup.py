#!/usr/bin/env python

from distutils.core import setup

setup(name='mwlr-geo-utils',
      version='1.1',
      description='Helpful utilities for working with geospatial data',
      author='Ben Jolly',
      author_email='bhjolly@gmail.com',
      url='https://github.com/manaakiwhenua/mwlr-geo-utils',
      scripts=[
        'bin/ext_to_poly.py',
        'bin/mw-extent.py',
        'bin/mw-gcptransform.py',
        'bin/mw-gdalvalidate.py',
        'bin/mw-hdfeosgetbands.py',
        'bin/mw-rasterize.py',
        'bin/mw-rasterstats.py',
        'bin/mw-rioscalc.py',
        'bin/mw-setbanddescr.py',
        'bin/mw-setvrtband.sh',
        ],
     )
