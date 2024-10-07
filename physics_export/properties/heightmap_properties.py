import bpy
from bpy.props import (
    FloatProperty,
    IntProperty,
    EnumProperty,
)

class HeightmapSettings(bpy.types.PropertyGroup):
    amplitude: FloatProperty(
        name="Amplitude",
        default=1.0,
        min=0.0,
        description="Height scale of the heightmap"
    )
    resolution: IntProperty(
        name="Resolution",
        default=10,
        min=1,
        description="Subdivision level for the face"
    )
    noise_type: EnumProperty(
        name="Noise Type",
        items=[
            ('FBM', "Fractal Brownian Motion", ""),
            ('PERLIN', "Perlin Noise", ""),
            ('SINE', "Sine Wave", ""),
            ('SQUARE', "Square Wave", "")
        ],
        default='FBM',
        description="Type of noise function to use"
    )
    octaves: IntProperty(
        name="Octaves",
        default=4,
        min=1,
        description="Number of octaves for FBM noise"
    )
    persistence: FloatProperty(
        name="Persistence",
        default=0.5,
        min=0.0,
        description="Persistence for FBM noise"
    )
    lacunarity: FloatProperty(
        name="Lacunarity",
        default=2.0,
        min=0.0,
        description="Lacunarity for FBM noise"
    )
