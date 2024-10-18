import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty, IntProperty

class HeightmapSettings(bpy.types.PropertyGroup):
    amplitude: FloatProperty(
        name="Amplitude",
        description="Heightmap amplitude",
        default=1.0,
        min=0.0,
        max=10.0
    )
    resolution: IntProperty(
        name="Resolution",
        description="Subdivision resolution",
        default=10,
        min=1,
        max=100
    )
    noise_type: EnumProperty(
        name="Noise Type",
        description="Type of noise to use",
        items=[
            ('FBM', "Fractal Brownian Motion", ""),
            ('PERLIN', "Perlin Noise", ""),
            ('SINE', "Sine Wave", ""),
            ('SQUARE', "Square Wave", ""),
            ('GABOR', "Gabor Noise", "")
        ],
        default='FBM'
    )
    octaves: IntProperty(
        name="Octaves",
        description="Number of noise octaves (for FBM)",
        default=4,
        min=1,
        max=10
    )
    H: FloatProperty(
        name="Fractal Increment (H)",
        description="Fractal increment controlling the roughness (for FBM)",
        default=0.5,
        min=0.0,
        max=1.0
    )
    lacunarity: FloatProperty(
        name="Lacunarity",
        description="Lacunarity of the noise (for FBM)",
        default=2.0,
        min=0.0,
        max=5.0
    )
    persistence: FloatProperty(
        name="Persistence",
        description="Controls the amplitude of each successive octave",
        default=0.5,
        min=0.0,
        max=1.0
    )
    # Add additional properties for Gabor noise if necessary
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
        min=0.0,
        max=10.0
    )
    power_spectrum: FloatProperty(
        name="Power Spectrum",
        description="Power spectrum for Gabor noise",
        default=1.0,
        min=0.0,
        max=10.0
    )