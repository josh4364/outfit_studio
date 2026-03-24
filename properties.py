import bpy

class OutfitStudioOutfitItem(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
        description="Collection containing the outfit items"
    )
    enabled: bpy.props.BoolProperty(
        name="Enabled",
        default=True,
        description="Whether to include this outfit in the bulk export"
    )

class OutfitStudioSettings(bpy.types.PropertyGroup):
    export_dir: bpy.props.StringProperty(
        name="Export Folder",
        description="Directory to export the files to",
        default="",
        subtype='DIR_PATH'
    )
    
    base_name: bpy.props.StringProperty(
        name="Base Name",
        description="Base name for the exported files",
        default="Model"
    )
    
    base_collection: bpy.props.PointerProperty(
        name="Base Collection",
        type=bpy.types.Collection,
        description="Collection containing the base model and armature"
    )

    include_base: bpy.props.BoolProperty(
        name="Include Base Meshes",
        description="Include meshes from the base collection in outfit exports",
        default=False
    )
    
    outfits: bpy.props.CollectionProperty(
        type=OutfitStudioOutfitItem,
        name="Outfits"
    )
    
    active_outfit_index: bpy.props.IntProperty(
        name="Active Outfit Index",
        default=0
    )
    
    export_format: bpy.props.EnumProperty(
        name="Export Format",
        items=[
            ('GLB', "GLB (.glb)", "Export as GLTF binary"),
            ('GLTF_SEPARATE', "GLTF Separate (.gltf)", "Export as GLTF with separate .bin and textures (useful for debugging)"),
            ('FBX', "FBX (.fbx)", "Export as FBX"),
        ],
        default='GLB'
    )

def register():
    bpy.utils.register_class(OutfitStudioOutfitItem)
    bpy.utils.register_class(OutfitStudioSettings)
    bpy.types.Scene.outfit_studio = bpy.props.PointerProperty(type=OutfitStudioSettings)

def unregister():
    del bpy.types.Scene.outfit_studio
    bpy.utils.unregister_class(OutfitStudioSettings)
    bpy.utils.unregister_class(OutfitStudioOutfitItem)
