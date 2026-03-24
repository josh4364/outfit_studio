import bpy
import os
import shutil

class OUTFITSTUDIO_OT_AddOutfit(bpy.types.Operator):
    bl_idname = "outfit_studio.add_outfit"
    bl_label = "Add Outfit"
    bl_description = "Add a new collection to the outfits list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.outfit_studio
        settings.outfits.add()
        settings.active_outfit_index = len(settings.outfits) - 1
        return {'FINISHED'}

class OUTFITSTUDIO_OT_RemoveOutfit(bpy.types.Operator):
    bl_idname = "outfit_studio.remove_outfit"
    bl_label = "Remove Outfit"
    bl_description = "Remove the selected collection from the outfits list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.outfit_studio
        if settings.active_outfit_index >= 0 and settings.active_outfit_index < len(settings.outfits):
            settings.outfits.remove(settings.active_outfit_index)
            settings.active_outfit_index = max(0, settings.active_outfit_index - 1)
        return {'FINISHED'}

class OUTFITSTUDIO_OT_BatchExport(bpy.types.Operator):
    bl_idname = "outfit_studio.batch_export"
    bl_label = "Batch Export Outfits"
    bl_description = "Export base and variants using temporary scenes for absolute isolation"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        settings = context.scene.outfit_studio
        original_scene = context.scene
        
        if not settings.export_dir:
            self.report({'ERROR'}, "Export Directory not set!")
            return {'CANCELLED'}
        if not settings.base_collection:
            self.report({'ERROR'}, "Base Collection not set!")
            return {'CANCELLED'}
            
        export_abs_path = bpy.path.abspath(settings.export_dir)
        export_format = settings.export_format
        base_name = settings.base_name
        
        if not os.path.exists(export_abs_path):
            os.makedirs(export_abs_path)

        try:
            # 1. Identify Main Armature
            armatures = [obj for obj in settings.base_collection.all_objects if obj.type == 'ARMATURE']
            if not armatures:
                self.report({'ERROR'}, "No Armature found in Base Collection!")
                return {'CANCELLED'}
            main_armature_name = armatures[0].name

            # 2. Identify All Outfit Objects
            all_outfit_collections = [o.collection for o in settings.outfits if o.collection]
            all_outfit_objects_names = set()
            for col in all_outfit_collections:
                for obj in col.all_objects:
                    all_outfit_objects_names.add(obj.name)

            # 3. Define helper for hierarchy extraction
            def get_hierarchy_names(obj_names):
                full = set(obj_names)
                for name in obj_names:
                    obj = bpy.data.objects.get(name)
                    if not obj: continue
                    curr = obj.parent
                    while curr:
                        full.add(curr.name)
                        curr = curr.parent
                return full

            # --- EXPORT LOOP ---
            
            # A. Export Base
            base_objs_names = [obj.name for obj in settings.base_collection.all_objects 
                               if obj.name not in all_outfit_objects_names]
            self.export_with_temp_scene(context, base_name, get_hierarchy_names(base_objs_names), 
                                        main_armature_name, export_abs_path, export_format)

            # B. Export Outfits
            for outfit in settings.outfits:
                if outfit.enabled and outfit.collection:
                    if settings.include_base:
                        # Include base meshes that aren't part of any specific outfit collection
                        struct_names = [obj.name for obj in settings.base_collection.all_objects 
                                        if obj.name not in all_outfit_objects_names]
                    else:
                        # Exclude all meshes from base collection (default behavior)
                        struct_names = [obj.name for obj in settings.base_collection.all_objects 
                                        if obj.type != 'MESH' and obj.name not in all_outfit_objects_names]
                    
                    outfit_mesh_names = [obj.name for obj in outfit.collection.all_objects if obj.type == 'MESH']
                    
                    target_names = get_hierarchy_names(struct_names + outfit_mesh_names)
                    file_name = f"{base_name}-{outfit.collection.name}"
                    
                    self.export_with_temp_scene(context, file_name, target_names, 
                                                main_armature_name, export_abs_path, export_format)

            self.report({'INFO'}, "Bulk Export Complete!")
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
        finally:
            context.window.scene = original_scene
            
        return {'FINISHED'}

    def export_with_temp_scene(self, context, file_name, object_names, armature_name, export_abs_path, export_format):
        # Create a completely empty new scene
        temp_scene = bpy.data.scenes.new(name="OS_Temp_Export")
        context.window.scene = temp_scene
        
        linked_objs = []
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if obj:
                temp_scene.collection.objects.link(obj)
                linked_objs.append(obj)
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in linked_objs:
            obj.select_set(True)
        
        main_armature = bpy.data.objects.get(armature_name)
        if main_armature:
            context.view_layer.objects.active = main_armature

        # RUN THE ACTUAL EXPORT
        self.run_export(context, file_name, linked_objs, export_abs_path, export_format)
        
        # Cleanup: Delete the temp scene
        bpy.data.scenes.remove(temp_scene)

    def copy_textures(self, objects, export_abs_path):
        texture_dir = os.path.join(export_abs_path, "textures")
        if not os.path.exists(texture_dir):
            os.makedirs(texture_dir)
        seen_paths = set()
        for obj in objects:
            if obj.type != 'MESH': continue
            for slot in obj.material_slots:
                if not slot.material or not slot.material.use_nodes: continue
                for node in slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        img_path = bpy.path.abspath(node.image.filepath)
                        if os.path.exists(img_path) and img_path not in seen_paths:
                            try:
                                shutil.copy2(img_path, texture_dir)
                                seen_paths.add(img_path)
                            except: pass

    def run_export(self, context, file_name, objects_to_export, export_abs_path, export_format):
        if export_format == 'FBX':
            extension = ".fbx"
        elif export_format == 'GLTF_SEPARATE':
            extension = ".gltf"
        else:
            extension = ".glb"
            
        filepath = os.path.join(export_abs_path, file_name + extension)
        
        # Log the full path to aid debugging
        self.report({'INFO'}, f"Writing to: {filepath}")
        
        self.report({'INFO'}, f"--- Exporting: {file_name} ---")
        for obj in sorted(objects_to_export, key=lambda x: x.name):
            p = obj.parent.name if obj.parent else "None"
            self.report({'INFO'}, f"  {obj.name} [Type: {obj.type}, Parent: {p}]")

        if export_format in {'GLB', 'GLTF_SEPARATE'}:
            fmt = 'GLTF_SEPARATE' if export_format == 'GLTF_SEPARATE' else 'GLB'
            bpy.ops.export_scene.gltf(
                'EXEC_DEFAULT',
                filepath=filepath,
                export_format=fmt,
                use_selection=True
            )
        else:
            self.copy_textures(objects_to_export, export_abs_path)
            bpy.ops.export_scene.fbx(
                'EXEC_DEFAULT',
                filepath=filepath,
                use_selection=True
            )

def register():
    bpy.utils.register_class(OUTFITSTUDIO_OT_AddOutfit)
    bpy.utils.register_class(OUTFITSTUDIO_OT_RemoveOutfit)
    bpy.utils.register_class(OUTFITSTUDIO_OT_BatchExport)

def unregister():
    bpy.utils.unregister_class(OUTFITSTUDIO_OT_BatchExport)
    bpy.utils.unregister_class(OUTFITSTUDIO_OT_RemoveOutfit)
    bpy.utils.unregister_class(OUTFITSTUDIO_OT_AddOutfit)
