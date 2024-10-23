import bpy
from bpy.props import FloatProperty, IntProperty, EnumProperty, StringProperty, BoolProperty
from bpy.types import PropertyGroup

class HeightmapSettings(PropertyGroup):
    """Settings for heightmap generation"""

    amplitude: FloatProperty(
        name="Amplitude",
        description="Amplitude of the heightmap",
        default=1.0,
        min=0.0,
        max=10.0
    )

    resolution: IntProperty(
        name="Resolution",
        description="Number of subdivisions along each axis",
        default=10,
        min=1,
        max=100
    )

    noise_type: EnumProperty(
        name="Noise Type",
        description="Type of noise to generate the heightmap",
        items=[
            ('FBM', "Fractional Brownian Motion", ""),
            ('PERLIN', "Perlin Noise", ""),
            ('SINE', "Sine Wave", ""),
            ('SQUARE', "Square Wave", ""),
            ('GABOR', "Gabor Noise", ""),
        ],
        default='PERLIN'
    )

    # Additional properties for specific noise types
    H: FloatProperty(
        name="H",
        description="Hurst exponent for FBM noise",
        default=0.5,
        min=0.0,
        max=1.0
    )

    lacunarity: FloatProperty(
        name="Lacunarity",
        description="Lacunarity for FBM noise",
        default=2.0,
        min=1.0,
        max=10.0
    )

    octaves: IntProperty(
        name="Octaves",
        description="Number of octaves for FBM noise",
        default=4,
        min=1,
        max=10
    )

    orientation: FloatProperty(
        name="Orientation",
        description="Orientation for Gabor noise",
        default=0.0,
        min=0.0,
        max=360.0
    )

    bandwidth: FloatProperty(
        name="Bandwidth",
        description="Bandwidth for Gabor noise",
        default=1.0,
        min=0.1,
        max=10.0
    )

    power_spectrum: FloatProperty(
        name="Power Spectrum",
        description="Power spectrum for Gabor noise",
        default=1.0,
        min=0.1,
        max=10.0
    )

    # Properties for Normal Map to Displacement Map conversion
    normal_map: StringProperty(
        name="Normal Map",
        description="Path to the normal map image",
        default="",
        subtype='FILE_PATH'
    )

    project_path: StringProperty(
        name="Project Path",
        description="Directory where the displacement map will be saved",
        default="//",
        subtype='DIR_PATH'
    )

    # New properties for contrast and inversion
    contrast: FloatProperty(
        name="Contrast",
        description="Adjust the contrast of the displacement map",
        default=1.0,
        min=0.0,
        max=10.0
    )

    invert_displacement: BoolProperty(
        name="Invert Displacement",
        description="Invert the displacement map values",
        default=False
    )
