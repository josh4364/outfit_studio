import bpy

class OUTFITSTUDIO_UL_OutfitList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="")
            if item.collection:
                row.label(text=item.collection.name, icon='OUTLINER_COLLECTION')
            else:
                row.label(text="(No Collection Selected)", icon='ERROR')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class OUTFITSTUDIO_PT_MainPanel(bpy.types.Panel):
    bl_label = "Outfit Studio"
    bl_idname = "OUTFITSTUDIO_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Outfit Studio'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.outfit_studio

        # Global Settings
        col = layout.column(align=True)
        col.label(text="Global Settings", icon='SETTINGS')
        box = col.box()
        box.prop(settings, "base_name")
        box.prop(settings, "export_dir")
        
        row = box.row(align=True)
        row.prop(settings, "export_format", text="Format")
        
        # Helper to open standard exporter for configuration
        if settings.export_format == 'FBX':
            row.operator("export_scene.fbx", text="", icon='PREFERENCES').filepath = "temp"
        else:
            # Both GLB and GLTF_EMBEDDED use the same GLTF exporter UI
            row.operator("export_scene.gltf", text="", icon='PREFERENCES').filepath = "temp"
            
        box.label(text="Settings will be inherited from the standard exporter.", icon='INFO')
        
        layout.separator()

        # Base Collection
        col = layout.column(align=True)
        col.label(text="Base Character", icon='OUTLINER_OB_ARMATURE')
        box = col.box()
        box.prop(settings, "base_collection", text="Base Collection")
        box.prop(settings, "include_base", text="Include Base")
        
        layout.separator()

        # Outfit List
        col = layout.column(align=True)
        col.label(text="Outfits", icon='MOD_CLOTH')
        
        row = col.row()
        row.template_list("OUTFITSTUDIO_UL_OutfitList", "", settings, "outfits", settings, "active_outfit_index")
        
        col_buttons = row.column(align=True)
        col_buttons.operator("outfit_studio.add_outfit", icon='ADD', text="")
        col_buttons.operator("outfit_studio.remove_outfit", icon='REMOVE', text="")
        
        # Detail view for the selected outfit to allow easy collection assignment
        if len(settings.outfits) > 0 and settings.active_outfit_index >= 0:
            active_outfit = settings.outfits[settings.active_outfit_index]
            box = col.box()
            box.prop(active_outfit, "collection", text="Selected Outfit")
        
        layout.separator()

        # Export Button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("outfit_studio.batch_export", icon='EXPORT', text="Batch Export Outfits")

def register():
    bpy.utils.register_class(OUTFITSTUDIO_UL_OutfitList)
    bpy.utils.register_class(OUTFITSTUDIO_PT_MainPanel)

def unregister():
    unregister_classes = [OUTFITSTUDIO_UL_OutfitList, OUTFITSTUDIO_PT_MainPanel]
    for cls in unregister_classes:
        bpy.utils.unregister_class(cls)
