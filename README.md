Simple addon to bulk export avatars plus their outfits as independent glb or fbx files.
Menu is in the sidebar of the 3d view like most addons.

* Select the base collection which contains your avatars 
`Armature/Body`

* Then move your clothing into their own collections. 
 * Example would be Jeans, which are at `Armature/Jeans`
* Then add that "Jeans" collection to the outfits list.
Now when you hit export your output directory will have:
model.fbx
model-jeans.fbx

when imported into unity, both will have the same armature so you can use stuff like modular avatar or vrcfury to merge the armatures and attach the outfit.
