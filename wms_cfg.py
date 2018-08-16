import re
# Static config for the wms metadata.

response_cfg = {
    "Access-Control-Allow-Origin": "*",  # CORS header
}

s3_path_pattern = re.compile('L8/(?P<path>[0-9]*)')

service_cfg = {
    # Required config
    "title": "WMS server for Australian Landsat Datacube",
    "url": "http://9xjfk12.nexus.csiro.au/datacube_wms",
    "published_CRSs": {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
        },
        "EPSG:4326": {  # WGS-84
            "geographic": True,
        },
        "EPSG:3577": {  # GDA-94, internal representation
            "geographic": False,
            "horizontal_coord": "easting",
            "vertical_coord": "northing",
        },
    },

    # Technically optional config, but strongly recommended
    "layer_limit": 1,
    "max_width": 512,
    "max_height": 512,

    # Optional config - may be set to blank/empty
    "abstract": """Historic Landsat imagery for Australia.""",
    "keywords": [
        "landsat",
        "australia",
        "time-series",
    ],
    "contact_info": {
        "person": "David Gavin",
        "organisation": "Geoscience Australia",
        "position": "Technical Lead",
        "address": {
            "type": "postal",
            "address": "GPO Box 378",
            "city": "Canberra",
            "state": "ACT",
            "postcode": "2906",
            "country": "Australia",
        },
        "telephone": "+61 2 1234 5678",
        "fax": "+61 2 1234 6789",
        "email": "test@example.com",
    },
    "fees": "",
    "access_constraints": "",
}

layer_cfg = [
    # Layer Config is a list of platform configs
    {
        # Name and title of the platform layer.
        # Platform layers are not mappable. The name is for internal server use only.
        "name": "LANDSAT_8",
        "title": "Landsat 8",
        "abstract": "Images from the Landsat 8 satellite",

        # Products available for this platform.
        # For each product, the "name" is the Datacube name, and the label is used
        # to describe the label to end-users.
        "products": [
            {
                # Example for USGS Level 1 Cloud-Optimised GeoTiffs in the AWS PDS.
                "label": "USGS Level 1",
                "type": "surface radiance",
                "variant": "PDS",
                # The WMS name for the layer
                "name": "ls8_level1_usgs",
                # The Datacube name for the associated data product
                "product_name": "ls8_level1_usgs",
                # Pixel quality is stored in the same datacube product as the band data
                "pq_dataset": "ls8_level1_usgs",
                # The name of the measurement band for the pixel-quality product
                "pq_band": "quality",
                # Min zoom factor - sets the zoom level where the cutover from indicative polygons
                # to actual imagery occurs.
                "min_zoom_factor": 500.0,
                # The fill-colour of the indicative polygons when zoomed out.
                # Triplets (rgb) or quadruplets (rgba) of integers 0-255.
                "zoomed_out_fill_colour": [150, 180, 200, 160],
                # Time Zone.  In hours added to UTC (maybe negative)
                # Used for rounding off scene times to a date.
                # 9 is good value for imagery of Australia.
                "time_zone": 9,
                # Extent mask functions
                # Determines what portions of dataset is potentially meaningful data.
                # Multiple extent mask functions are required for this data.
                "extent_mask_func": [
                    lambda data, band: data["quality"] != 1,
                    lambda data, band: data[band] != data[band].attrs['nodata'],
                ],
                # Flags listed here are ignored in GetFeatureInfo requests.
                # (defaults to empty list)
                "ignore_info_flags": [],

                # Bands to include in time-dimension "pixel drill".
                # WARNING: This is highly inefficient in the current datacube architecture.
                #          Don't activate in production unless you really know what you're doing.
                # "band_drill": ["nir", "red", "green", "blue"],


                # Set to true if the band product dataset extents include nodata regions.
                "data_manual_merge": True,
                # Set to true if the pq product dataset extents include nodata regions.
                "pq_manual_merge": True,
                # Bands to always fetch from the Datacube, even if it is not used by the active style.
                # Useful for when a particular band is always needed for the extent_mask_func,
                "always_fetch_bands": [ "quality", ],
                # Apply corrections for solar angle, for "Level 1" products.
                "apply_solar_corrections": True,

                # A function that extracts the "sub-product" id (e.g. path number) from a dataset. Function should return a (small) integer
                # If None or not specified, the product has no sub-layers.
                "sub_product_extractor": lambda ds: int(s3_path_pattern.search(ds.uris[0]).group("path")),
                # A prefix used to describe the sub-layer in the GetCapabilities response.
                # E.g. sub-layer 109 will be described as "Landsat Path 109"
                "sub_product_label": "Landsat Path",

                # Styles.
                #
                # See band_mapper.py
                #
                # The various available spectral bands, and ways to combine them
                # into a single rgb image.
                # The examples here are ad hoc
                #
                # LS7:  http://www.indexdatabase.de/db/s-single.php?id=8
                # LS8:  http://www.indexdatabase.de/db/s-single.php?id=168
                "styles": [
                    # Examples of styles which are linear combinations of the available spectral bands.
                    #
                    {
                        "name": "simple_rgb",
                        "title": "Simple RGB",
                        "abstract": "Simple true-colour image, using the red, green and blue bands",
                        "components": {
                            "red": {
                                "red": 1.0
                            },
                            "green": {
                                "green": 1.0
                            },
                            "blue": {
                                "blue": 1.0
                            }
                        },
                        # The raw band value range to be compressed to an 8 bit range for the output image tiles.
                        # Band values outside this range are clipped to 0 or 255 as appropriate.
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "cloud_masked_rgb",
                        "title": "Simple RGB with cloud masking",
                        "abstract": "Simple true-colour image, using the red, green and blue bands, with cloud masking",
                        "components": {
                            "red": {
                                "red": 1.0
                            },
                            "green": {
                                "green": 1.0
                            },
                            "blue": {
                                "blue": 1.0
                            }
                        },
                        # PQ masking example
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud": False,
                                },
                            },
                        ],
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "extended_rgb",
                        "title": "Extended RGB",
                        "abstract": "Extended true-colour image, incorporating the coastal aerosol band",
                        "components": {
                            "red": {
                                "red": 1.0
                            },
                            "green": {
                                "green": 1.0
                            },
                            "blue": {
                                "blue": 0.6,
                                "coastal_aerosol": 0.4
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "wideband",
                        "title": "Wideband false-colour",
                        "abstract": "False-colour image, incorporating all available spectral bands",
                        "components": {
                            "red": {
                                "swir2": 0.255,
                                "swir1": 0.45,
                                "nir": 0.255,
                            },
                            "green": {
                                "nir": 0.255,
                                "red": 0.45,
                                "green": 0.255,
                            },
                            "blue": {
                                "green": 0.255,
                                "blue": 0.45,
                                "coastal_aerosol": 0.255,
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "infra_red",
                        "title": "False colour multi-band infra-red",
                        "abstract": "Simple false-colour image, using the near and short-wave infra-red bands",
                        "components": {
                            "red": {
                                "swir1": 1.0
                            },
                            "green": {
                                "swir2": 1.0
                            },
                            "blue": {
                                "nir": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "coastal_aerosol",
                        "title": "Spectral band 1 - Coastal aerosol",
                        "abstract": "Coastal aerosol band, approximately 435nm to 450nm",
                        "components": {
                            "red": {
                                "coastal_aerosol": 1.0
                            },
                            "green": {
                                "coastal_aerosol": 1.0
                            },
                            "blue": {
                                "coastal_aerosol": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "blue",
                        "title": "Spectral band 2 - Blue",
                        "abstract": "Blue band, approximately 453nm to 511nm",
                        "components": {
                            "red": {
                                "blue": 1.0
                            },
                            "green": {
                                "blue": 1.0
                            },
                            "blue": {
                                "blue": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "green",
                        "title": "Spectral band 3 - Green",
                        "abstract": "Green band, approximately 534nm to 588nm",
                        "components": {
                            "red": {
                                "green": 1.0
                            },
                            "green": {
                                "green": 1.0
                            },
                            "blue": {
                                "green": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "red",
                        "title": "Spectral band 4 - Red",
                        "abstract": "Red band, roughly 637nm to 672nm",
                        "components": {
                            "red": {
                                "red": 1.0
                            },
                            "green": {
                                "red": 1.0
                            },
                            "blue": {
                                "red": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "nir",
                        "title": "Spectral band 5 - Near infra-red",
                        "abstract": "Near infra-red band, roughly 853nm to 876nm",
                        "components": {
                            "red": {
                                "nir": 1.0
                            },
                            "green": {
                                "nir": 1.0
                            },
                            "blue": {
                                "nir": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "swir1",
                        "title": "Spectral band 6 - Short wave infra-red 1",
                        "abstract": "Short wave infra-red band 1, roughly 1575nm to 1647nm",
                        "components": {
                            "red": {
                                "swir1": 1.0
                            },
                            "green": {
                                "swir1": 1.0
                            },
                            "blue": {
                                "swir1": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "swir2",
                        "title": "Spectral band 7 - Short wave infra-red 2",
                        "abstract": "Short wave infra-red band 2, roughly 2117nm to 2285nm",
                        "components": {
                            "red": {
                                "swir2": 1.0
                            },
                            "green": {
                                "swir2": 1.0
                            },
                            "blue": {
                                "swir2": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    #
                    # Examples of non-linear heat-mapped styles.
                    {
                        "name": "ndvi",
                        "title": "NDVI",
                        "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndvi_cloudmask",
                        "title": "NDVI with cloud masking",
                        "abstract": "Normalised Difference Vegetation Index (with cloud masking) - a derived index that correlates well with the existence of vegetation",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud": False,
                                 },
                            },
                        ],
                    },
                    {
                        "name": "ndwi",
                        "title": "NDWI",
                        "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["green"] - data["nir"]) / (data["nir"] + data["green"]),
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndwi_cloudmask",
                        "title": "NDWI with cloud and cloud-shadow masking",
                        "abstract": "Normalised Difference Water Index (with cloud and cloud-shadow masking) - a derived index that correlates well with the existence of water",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["green"] - data["nir"]) / (data["nir"] + data["green"]),
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud": False,
                                },
                            },
                        ],
                    },
                    {
                        "name": "ndbi",
                        "title": "NDBI",
                        "abstract": "Normalised Difference Buildup Index - a derived index that correlates with the existence of urbanisation",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["swir2"] - data["nir"]) / (data["swir2"] + data["nir"]),
                        "needed_bands": ["swir2", "nir"],
                        "range": [0.0, 1.0],
                    },
                    # Mask layers - examples of how to display raw pixel quality data.
                    # This works by creatively mis-using the Heatmap style class.
                    {
                        "name": "cloud_mask",
                        "title": "Cloud Mask",
                        "abstract": "Highlight pixels with cloud.",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.1,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        # Mask flags normally describe which areas SHOULD be shown.
                        # (i.e. pixels for which any of the declared flags are true)
                        # pq_mask_invert is intended to invert this logic.
                        # (i.e. pixels for which none of the declared flags are true)
                        #
                        # i.e. Specifying like this shows pixels which are not clouds in either metric.
                        #      Specifying "cloud" and setting the "pq_mask_invert" to False would
                        #      show pixels which are not clouds in both metrics.
                        "pq_masks": [
                            {
                                "invert": True,
                                "flags": {
                                    "cloud": False,
                                },
                            },
                        ],
                    },
                    # Hybrid style - mixes a linear mapping and a heat mapped index
                    {
                        "name": "rgb_ndvi",
                        "title": "NDVI plus RGB",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                        "components": {
                            "red": {
                                "red": 1.0
                            },
                            "green": {
                                "green": 1.0
                            },
                            "blue": {
                                "blue": 1.0
                            }
                        },
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "rgb_ndvi_cloudmask",
                        "title": "NDVI plus RGB (Cloud masked)",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB and cloud masked) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                        "components": {
                            "red": {
                                "red": 1.0
                            },
                            "green": {
                                "green": 1.0
                            },
                            "blue": {
                                "blue": 1.0
                            }
                        },
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud": False,
                                },
                            },
                        ],
                        "scale_range": [ 9500, 22000 ],
                    }
                ],
                # Default style (if request does not specify style)
                # MUST be defined in the styles list above.

                # (Looks like Terria assumes this is the first style in the list, but this is
                #  not required by the standard.)
                "default_style": "simple_rgb",
            },
        ],
    },
]

to_be_added_to_layer_cfg = {
    "name": "LANDSAT_7",
    "title": "Landsat 7",
    "abstract": "Images from the Landsat 7 satellite",

    "products": [
        {
            "label": "NBAR-T",
            "type": "surface reflectance",
            "variant": "terrain corrected",
            "name": "ls7_nbart_albers",
            "product_name": "ls7_nbart_albers",
            "pq_dataset": "ls7_pq_albers",
            "pq_band": "pixelquality",
            "pq_mask_flags": {
                "contiguous": True
            },
            "min_zoom_factor": 500.0
        },
    ],
    "styles": [
        {
            "name": "simple_rgb",
            "title": "Simple RGB",
            "abstract": "Simple true-colour image, using the red, green and blue bands",
            "components": {
                "red": {
                    "red": 1.0
                },
                "green": {
                    "green": 1.0
                },
                "blue": {
                    "blue": 1.0
                }
            },
            "scale_range": [0.0, 3000.0]
        },
        {
            "name": "wideband",
            "title": "Wideband false-colour",
            "abstract": "False-colour image, incorporating all available spectral bands",
            "components": {
                "red": {
                    "swir2": 0.5,
                    "swir1": 0.5,
                },
                "green": {
                    "nir": 0.5,
                    "red": 0.5,
                },
                "blue": {
                    "green": 0.5,
                    "blue": 0.5,
                }
            },
            "scale_range": [0.0, 3000.0]
        },
        {
            "name": "infra_red",
            "title": "False colour multi-band infra-red",
            "abstract": "Simple false-colour image, using the near and short-wave infra-red bands",
            "components": {
                "red": {
                    "swir1": 1.0
                },
                "green": {
                    "swir2": 1.0
                },
                "blue": {
                    "nir": 1.0
                }
            },
            "scale_factor": 12.0
        },
        {
            "name": "blue",
            "title": "Spectral band 1 - Blue",
            "abstract": "Blue band, approximately 450nm to 520nm",
            "components": {
                "red": {
                    "blue": 1.0
                },
                "green": {
                    "blue": 1.0
                },
                "blue": {
                    "blue": 1.0
                }
            },
            "scale_factor": 12.0
        },
        {
            "name": "green",
            "title": "Spectral band 2 - Green",
            "abstract": "Green band, approximately 530nm to 610nm",
            "components": {
                "red": {
                    "green": 1.0
                },
                "green": {
                    "green": 1.0
                },
                "blue": {
                    "green": 1.0
                }
            },
            "scale_factor": 12.0
        },
        {
            "name": "red",
            "title": "Spectral band 3 - Red",
            "abstract": "Red band, roughly 630nm to 690nm",
            "components": {
                "red": {
                    "red": 1.0
                },
                "green": {
                    "red": 1.0
                },
                "blue": {
                    "red": 1.0
                }
            },
            "scale_factor": 12.0
        },
        {
            "name": "nir",
            "title": "Spectral band 4 - Near infra-red",
            "abstract": "Near infra-red band, roughly 780nm to 840nm",
            "components": {
                "red": {
                    "nir": 1.0
                },
                "green": {
                    "nir": 1.0
                },
                "blue": {
                    "nir": 1.0
                }
            },
            "scale_factor": 12.0
        },
        {
            "name": "swir1",
            "title": "Spectral band 5 - Short wave infra-red 1",
            "abstract": "Short wave infra-red band 1, roughly 1550nm to 1750nm",
            "components": {
                "red": {
                    "swir1": 1.0
                },
                "green": {
                    "swir1": 1.0
                },
                "blue": {
                    "swir1": 1.0
                }
            },
            "scale_factor": 12.0
        },
        {
            "name": "swir2",
            "title": "Spectral band 6 - Short wave infra-red 2",
            "abstract": "Short wave infra-red band 2, roughly 2090nm to 2220nm",
            "components": {
                "red": {
                    "swir2": 1.0
                },
                "green": {
                    "swir2": 1.0
                },
                "blue": {
                    "swir2": 1.0
                }
            },
            "scale_factor": 12.0
        }
    ],
    "default_style": "simple_rgb",
}
