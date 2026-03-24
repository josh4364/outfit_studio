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
    bl_description = "Export base and variants for all enabled outfits"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        settings = context.scene.outfit_studio
        
        if not settings.export_dir:
            self.report({'ERROR'}, "Export Directory not set!")
            return {'CANCELLED'}
        
        if not settings.base_collection:
            self.report({'ERROR'}, "Base Collection not set!")
            return {'CANCELLED'}
            
        export_path = bpy.path.abspath(settings.export_dir)
        if not os.path.exists(export_path):
            os.makedirs(export_path)
            
        # Store current selection and active object
        old_selection = context.selected_objects[:]
        old_active = context.active_object
        
        # Store original exclusion states of outfit collections
        view_layer = context.view_layer
        original_excludes = {}
        original_obj_visibility = {} # Store (hide_get, hide_viewport)
        
        def set_collection_exclude(collection, exclude):
            def recurse(layer_col):
                if layer_col.collection == collection:
                    layer_col.exclude = exclude
                    return True
                for child in layer_col.children:
                    if recurse(child):
                        return True
                return False
            recurse(view_layer.layer_collection)

        def get_collection_exclude(collection):
            def recurse(layer_col):
                if layer_col.collection == collection:
                    return layer_col.exclude
                for child in layer_col.children:
                    val = recurse(child)
                    if val is not None:
                        return val
                return None
            return recurse(view_layer.layer_collection)

        def make_objects_visible(objects):
            for obj in objects:
                if obj not in original_obj_visibility:
                    original_obj_visibility[obj] = (obj.hide_get(), obj.hide_viewport)
                obj.hide_set(False)
                obj.hide_viewport = False

        # 0. Cache and Exclude all outfit collections initially
        all_outfit_collections = [o.collection for o in settings.outfits if o.collection]
        for col in all_outfit_collections:
            original_excludes[col] = get_collection_exclude(col)
            set_collection_exclude(col, True)

        try:
            # 1. Export Base Model
            all_outfit_objects = set()
            for col in all_outfit_collections:
                all_outfit_objects.update(col.all_objects)

            base_objs = [obj for obj in settings.base_collection.all_objects if obj not in all_outfit_objects]
            
            make_objects_visible(base_objs)
            self.select_objects(context, base_objs)
            self.run_export(context, settings.base_name, base_objs)
            
            # 2. Export each outfit
            for outfit in settings.outfits:
                if outfit.enabled and outfit.collection:
                    # Temporarily include THIS outfit collection in view layer
                    set_collection_exclude(outfit.collection, False)
                    
                    armatures = [obj for obj in settings.base_collection.all_objects if obj.type == 'ARMATURE']
                    outfit_objs = list(outfit.collection.all_objects)
                    
                    all_to_export = armatures + outfit_objs
                    make_objects_visible(all_to_export)
                    self.select_objects(context, all_to_export)
                    
                    suffix = outfit.collection.name
                    file_name = f"{settings.base_name}-{suffix}"
                    self.run_export(context, file_name, all_to_export)
                    
                    # Re-exclude for next iteration
                    set_collection_exclude(outfit.collection, True)
                    
            self.report({'INFO'}, "Bulk Export Complete!")
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
        finally:
            # Restore original object visibility
            for obj, (hide_get, hide_viewport) in original_obj_visibility.items():
                try:
                    obj.hide_set(hide_get)
                    obj.hide_viewport = hide_viewport
                except:
                    pass

            # Restore original exclusion states
            for col, state in original_excludes.items():
                if state is not None:
                    set_collection_exclude(col, state)

            # Restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in old_selection:
                try:
                    obj.select_set(True)
                except:
                    pass
            if old_active:
                context.view_layer.objects.active = old_active
            
        return {'FINISHED'}

    def select_objects(self, context, objects):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            try:
                obj.select_set(True)
            except:
                pass # Might be hidden/excluded
        if objects:
            try:
                context.view_layer.objects.active = objects[0]
            except:
                pass

    def copy_textures(self, objects, export_abs_path):
        texture_dir = os.path.join(export_abs_path, "textures")
        if not os.path.exists(texture_dir):
            os.makedirs(texture_dir)
            
        seen_paths = set()
        for obj in objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                if not slot.material or not slot.material.use_nodes:
                    continue
                for node in slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        img_path = bpy.path.abspath(node.image.filepath)
                        if os.path.exists(img_path) and img_path not in seen_paths:
                            try:
                                shutil.copy2(img_path, texture_dir)
                                seen_paths.add(img_path)
                            except Exception as e:
                                print(f"Outfit Studio: Failed to copy texture {img_path}: {e}")

    def run_export(self, context, file_name, objects_to_export):
        settings = context.scene.outfit_studio
        extension = ".glb" if settings.export_format == 'GLB' else ".fbx"
        export_abs_path = bpy.path.abspath(settings.export_dir)
        filepath = os.path.join(export_abs_path, file_name + extension)
        
        if settings.export_format == 'GLB':
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLB',
                use_selection=True,
                export_apply=True # Ensure modifiers etc are applied if desired
            )
        else:
            # Copy textures for FBX compatibility with Unity
            self.copy_textures(objects_to_export, export_abs_path)
            
            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True,
                axis_forward='-Z',
                axis_up='Y',
                apply_scale_options='FBX_SCALE_ALL'
            )

def register():
    bpy.utils.register_class(OUTFITSTUDIO_OT_AddOutfit)
    bpy.utils.register_class(OUTFITSTUDIO_OT_RemoveOutfit)
    bpy.utils.register_class(OUTFITSTUDIO_OT_BatchExport)

def unregister():
    bpy.utils.unregister_class(OUTFITSTUDIO_OT_BatchExport)
    bpy.utils.unregister_class(OUTFITSTUDIO_OT_RemoveOutfit)
    bpy.utils.unregister_class(OUTFITSTUDIO_OT_AddOutfit)
