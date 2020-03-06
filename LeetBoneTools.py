# Leet Bone Tools
# Created By Colin Leet for Blender 2.8

# GPL-3.0 License

# This blender 2.8 add-on is meant to making animating sets of bones on a character faster and easier.
# This tool's primary use is to make saved (cached) selections of bones on a per armature basis.
# It also contains some tools to add, delete, and reset key-frames for selected bones on the current frame.

# This blender add-on only runs in pose mode.

# This tool-set's panel and pie menu shows-up only when an armature is selected in pose mode:
# the tool-set's panel is under 3D View -> Item,
# and to use the pie menu hold control and left click in a 3d View.
#
# Cached bone selections are created, edited, and deleted only in the tool's 3d-view panel, not in the pie menu.
# Cached bone selections are saved in an auxiliary text file in the same directory as the blend file.
# The user can choose to add to, or replace, their current selection with cached bone selections.
# The user can also choose to focus on the selected bones when using the tool modify bone selections.

# Original script layout derived from: https://blender.stackexchange.com/q/57306/3710

import bpy
import os  # Used for cached selection saving/loading
from ntpath import split as ntSplit  # Splits file path into file name and directory
from bpy.utils import register_class, unregister_class
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

bl_info = {
    "name": "Leet Bone Tools",
    "description": "Contains some useful functions for animating bones.",
    "author": "Colin Leet",
    "version": (1, 0, 0),
    "blender": (2, 82, 0),
    "location": "3D View > Item",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/colinleet/Leet-Bone-Tools",
    "tracker_url": "",
    "category": "Development"
}


# ------------------------------------------------------------------------
#    Toolset Properties
# ------------------------------------------------------------------------

class LeetBoneToolsSettings(PropertyGroup):
    EffectLoc: BoolProperty(
        name="Loc",
        description="Makes Leet Bone Tools Effect Location",
        default=True
    )

    EffectRot: BoolProperty(
        name="Rot",
        description="Makes Leet Bone Tools Effect Rotation",
        default=True
    )

    EffectScale: BoolProperty(
        name="Scale",
        description="Makes Leet Bone Tools Effect Scale",
        default=False
    )

    ReplaceSelected: BoolProperty(
        name="Replace Selection",
        description="Replaces the selection instead of adding to it",
        default=False
    )

    DeleteCachesMode: BoolProperty(
        name="Delete Caches",
        description="Allow you to delete selection caches",
        default=False
    )

    AutoSaveBoneCaches: BoolProperty(
        name="Autosave Bone Caches",
        description="When true any changes to bone groups will automatically be saved",
        default=True
    )

    EditCaches: BoolProperty(
        name="Add/Edit Bone Selection Caches",
        description="Enables UI elements to edit or add new bones selection caches in this panel",
        default=True
    )

    ViewPieTools: BoolProperty(
        name="View Tools",
        description="This will show leet bone tools in the pie menu, and make the cache list a list",
        default=True
    )

    ViewPieFrameKeying: BoolProperty(
        name="Bone Keying Tools",
        description="This will show the current frame bone keying tools in the pie menu",
        default=True
    )

    ViewPieCursorSnapTools: BoolProperty(
        name="Snap To Cursor Tools",
        description="This will show or hide the go to cursor tools when one bone is selected",
        default=False
    )

    FocusOnSelected: BoolProperty(
        name="Zoom To Selected",
        description="This will refocus the view to the selected objects",
        default=False
    )

    CurrArm: StringProperty(
        name="Skellolo",
        description="Skel with the cache",
        default="None"
    )

    NewCacheName: StringProperty(
        name="New Cache Name",
        description="The name for a new cached bone selection group",
        default=""
    )

    # Non-saved options
    CachedSelections = {}
    CachesOrder = {}


# ------------------------------------------------------------------------
#    Save Load Helper Functions
# ------------------------------------------------------------------------

def GetCWDAndFileName():
    # Returns the current cwd, and file name
    cwd, fileName = ntSplit(bpy.data.filepath)
    fileName = fileName.strip(".blend") + "-LeetBoneToolsSelections.txt"
    return (cwd, fileName)


# ------------------------------------------------------------------------
#    Operators - Cached Bone Selections / Saving / Loading
# ------------------------------------------------------------------------

class Leet_CacheBonesLoadDisk(Operator):
    bl_label = "Load Cached Bones From Disk"
    bl_idname = "leet.cached_bones_load_disk"

    def execute(self, context):
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # Saves the current matches to a file so they can be loaded.
        # boneTools.AttemptedLoadBoneCache = True
        cwd, fileName = GetCWDAndFileName()
        filePath = os.path.join(cwd, fileName)

        if os.path.exists(filePath):
            # Create the file
            openFile = open(filePath, 'r')
            d = eval(openFile.read())
            openFile.close()

            # Load the cache data
            for i in d[0].keys():
                scene.leetBoneToolsSettings.CachedSelections[i] = d[0][i]

            # Load the list order data
            for j in d[1].keys():
                scene.leetBoneToolsSettings.CachesOrder[j] = d[1][j]

        else:
            print("Could not find file to load... " + filePath)

        return {'FINISHED'}


class Leet_CacheBonesSaveDisk(Operator):
    bl_label = "Save Cached Bones To Disk"
    bl_idname = "leet.cached_bones_save_disk"

    def execute(self, context):
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # Saves the current matches to a file so they can be loaded.
        cwd, fileName = GetCWDAndFileName()
        filePath = os.path.join(cwd, fileName)

        # Create the file
        saveFile = open(filePath, 'w')
        fileContent = str([boneTools.CachedSelections, boneTools.CachesOrder])
        saveFile.write(str(fileContent))
        saveFile.close()

        return {'FINISHED'}


class Leet_CacheSelectedBones(Operator):
    bl_label = "Make New Cache Of Selected Bones"
    bl_idname = "leet.sel_bones_cache"

    def execute(self, context):
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # Save Arm Name
        boneTools.CurrArm = bpy.context.object.name
        newGroup = boneTools.NewCacheName

        # Cache the selected bones
        if len(bpy.context.selected_pose_bones) > 0:

            # Add new dict item for saved group
            boneTools.CachedSelections[boneTools.CurrArm][newGroup] = []
            boneTools.CachesOrder[boneTools.CurrArm].append(newGroup)

            for i in bpy.context.selected_pose_bones:
                boneTools.CachedSelections[boneTools.CurrArm][newGroup].append(i.name)

            # Save changes
            if boneTools.AutoSaveBoneCaches:
                bpy.ops.leet.cached_bones_save_disk()

        return {'FINISHED'}


class Leet_SelectCachedBonesSet(Operator):
    bl_label = "Select Cached Bones"
    bl_idname = "leet.cached_bones_sel"

    sel_group: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # Save Arm Name
        boneTools.CurrArm = bpy.context.object.name

        # Check valid input
        if self.sel_group == "":
            return {'FINISHED'}
        elif self.sel_group not in boneTools.CachedSelections[boneTools.CurrArm]:
            return {'FINISHED'}

        # Clear old selection?
        if boneTools.ReplaceSelected:
            bpy.ops.pose.select_all(action='DESELECT')

        # Select the cached bones
        for i in boneTools.CachedSelections[boneTools.CurrArm][self.sel_group]:
            b = bpy.data.objects[boneTools.CurrArm].data.bones[i]
            b.select = True

        # Should we focus on the selected objects?
        if boneTools.FocusOnSelected:
            bpy.ops.view3d.view_selected()

        return {'FINISHED'}

class Leet_CachedBoneMoveIndex(Operator):
    bl_label = "Move Index of Cached Bones"
    bl_idname = "leet.cached_bones_move_index"

    sel_group: bpy.props.StringProperty()
    move_up: bpy.props.BoolProperty()

    def execute(self, context):
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # Save Arm Name
        boneTools.CurrArm = bpy.context.object.name

        # Get arm cache count
        c = len(boneTools.CachesOrder[boneTools.CurrArm])

        if self.sel_group == "":
            return {'FINISHED'}
        elif self.sel_group not in boneTools.CachesOrder[boneTools.CurrArm]:
            return {'FINISHED'}
        elif c <= 1:
            return {'FINISHED'}

        # Switch the index
        modVal = len(boneTools.CachesOrder[boneTools.CurrArm])
        sel_index = boneTools.CachesOrder[boneTools.CurrArm].index(self.sel_group)
        if self.move_up:
            new_index = sel_index - 1
        else:
            new_index = sel_index + 1
        sel_index = sel_index % modVal
        new_index = new_index % modVal
        boneTools.CachesOrder[boneTools.CurrArm][sel_index],\
        boneTools.CachesOrder[boneTools.CurrArm][new_index] = boneTools.CachesOrder[boneTools.CurrArm][new_index],\
                                                              boneTools.CachesOrder[boneTools.CurrArm][sel_index]

        # Save changes
        if boneTools.AutoSaveBoneCaches:
            bpy.ops.leet.cached_bones_save_disk()

        return {'FINISHED'}


class Leet_DeleteCachedBonesSet(Operator):
    bl_label = "Delete Cached Bones"
    bl_idname = "leet.delete_cached_bones_set"

    sel_group: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # Save Arm Name
        boneTools.CurrArm = bpy.context.object.name

        if self.sel_group == "":
            return {'FINISHED'}
        elif self.sel_group not in boneTools.CachedSelections[boneTools.CurrArm]:
            return {'FINISHED'}

        # Delete the selection cache
        del boneTools.CachedSelections[boneTools.CurrArm][self.sel_group]
        ind = boneTools.CachesOrder[boneTools.CurrArm].index(self.sel_group)
        del boneTools.CachesOrder[boneTools.CurrArm][ind]

        # Save changes
        if boneTools.AutoSaveBoneCaches:
            bpy.ops.leet.cached_bones_save_disk()

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Operators - Selected Bones Keying and Resetting
# ------------------------------------------------------------------------

class Leet_ResetBones(Operator):
    bl_label = "Reset Bones"
    bl_idname = "leet.reset_bones"

    def execute(self, context):
        scene = context.scene

        # Reset transforms for the selected bones
        boneTools = scene.leetBoneToolsSettings

        if boneTools.EffectLoc:
            bpy.ops.pose.loc_clear()

        if boneTools.EffectRot:
            bpy.ops.pose.rot_clear()

        if boneTools.EffectScale:
            bpy.ops.pose.scale_clear()

        return {'FINISHED'}


class Leet_KeyBones(Operator):
    bl_label = "Key Bone"
    bl_idname = "leet.key_bones"

    def execute(self, context):
        scene = context.scene

        # Set keyfranes on the selected bones
        boneTools = scene.leetBoneToolsSettings

        if boneTools.EffectLoc:
            bpy.ops.anim.keyframe_insert_menu(type='Location')

        if boneTools.EffectRot:
            bpy.ops.anim.keyframe_insert_menu(type='Rotation')

        if boneTools.EffectScale:
            bpy.ops.anim.keyframe_insert_menu(type='Scaling')

        return {'FINISHED'}


class Leet_ClearKeyBones(Operator):
    bl_label = "Clear Keys"
    bl_idname = "leet.clear_key_bones"

    def execute(self, context):
        scene = context.scene

        # Set keyfranes on the selected bones
        boneTools = scene.leetBoneToolsSettings
        f = bpy.context.scene.frame_current

        for i in bpy.context.selected_pose_bones:
            if boneTools.EffectLoc:
                i.keyframe_delete('location', frame=f)

            if boneTools.EffectRot:
                i.keyframe_delete('rotation_euler', frame=f)
                i.keyframe_delete('rotation_quaternion', frame=f)

            if boneTools.EffectScale:
                i.keyframe_delete('scale', frame=f)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    3D View Tool Panel
# ------------------------------------------------------------------------

class OBJECT_PT_LeetBonePanel(Panel):
    bl_label = "Leet Bone Tools"
    bl_idname = "OBJECT_PT_LeetBonePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_context = "posemode"

    @classmethod
    def poll(self, context):
        # Only show panel when an armature is selected.
        if context.object is not None:
            return context.object.type == 'ARMATURE'
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        # ------------------------------------------------------------------------
        #    Move bone and Keying Opps
        # ------------------------------------------------------------------------

        # Set curr arm, and add it to the selection cache dict
        currArm = bpy.context.object.name
        if currArm not in boneTools.CachedSelections:
            boneTools.CachedSelections[currArm] = {}
        if currArm not in boneTools.CachesOrder:
            boneTools.CachesOrder[currArm] = []

        # Number of bones selected
        num_bones_selected = len(bpy.context.selected_pose_bones)
        bones_selected = num_bones_selected > 0
        caches_count = len(boneTools.CachedSelections[currArm])
        bones_cached = caches_count > 0

        # Keying Selected Bones Controls Current Frame Tools
        bo = "Bone" if num_bones_selected == 1 else "Bones"
        layout.label(text="{} {} Selected on {}".format(num_bones_selected, bo, currArm))
        effect_keys_row = layout.row()
        effect_keys_row.prop(boneTools, "EffectLoc")
        effect_keys_row.prop(boneTools, "EffectRot")
        effect_keys_row.prop(boneTools, "EffectScale")
        if bones_selected:
            bones_keying_opps_row = layout.row()
            bones_keying_opps_row.operator("leet.key_bones", icon="KEYTYPE_KEYFRAME_VEC")
            bones_keying_opps_row.operator("leet.clear_key_bones", icon="TRASH")
            bones_keying_opps_row.operator("leet.reset_bones", icon="FILE_REFRESH")

        else:
            layout.label(text="Select bone(s) to affect keying.")

        layout.separator()

        # ------------------------------------------------------------------------
        #    Caching Bone Selections
        # ------------------------------------------------------------------------

        # Cached Selection Label
        if not bones_cached:
            layout.label(text="No selections cached for {}".format(currArm))
            if not boneTools.EditCaches:
                layout.operator("leet.cached_bones_load_disk", icon="FILE_FOLDER")
            layout.prop(boneTools, "EditCaches", icon="SETTINGS")

        # Load or Delete Cached Selection Selection
        if bones_cached:
            # Button Actions Configuration
            sel_action_edit_row = layout.row()
            sel_action_edit_row.prop(boneTools, "ReplaceSelected", icon="SELECT_SET")
            sel_action_edit_row.prop(boneTools, "FocusOnSelected", icon="ZOOM_SELECTED")

            # List all of the bone groups for this arm with the targeted action
            for i in boneTools.CachesOrder[currArm]:
                # Naming of group
                size = len(boneTools.CachedSelections[currArm][i])
                b = "Bones" if size > 1 else "Bone"

                if boneTools.EditCaches:  # Delete Group
                    if boneTools.DeleteCachesMode:
                        op = layout.operator("leet.delete_cached_bones_set", icon="TRASH",
                                             text="{} ({} {})".format(i, size, b))
                        op.sel_group = i

                    else: # Move Caches
                        moveRow = layout.row()
                        moveRow.label(text="{} ({})".format(i, size))

                        if caches_count > 1: # Buttons to move up and down
                            opU = moveRow.operator("leet.cached_bones_move_index", text="", icon="SORT_DESC")
                            opD = moveRow.operator("leet.cached_bones_move_index", text="", icon="SORT_ASC")
                            opU.sel_group, opD.sel_group = i, i
                            opU.move_up, opD.move_up = True, False

                else:  # Select Group
                    ico = "SELECT_SET" if boneTools.ReplaceSelected else "SELECT_EXTEND"
                    op = layout.operator("leet.cached_bones_sel", text="{} ({} {})".format(i, size, b), icon=ico)
                    op.sel_group = i

            layout.prop(boneTools, "EditCaches", icon="SETTINGS")

        # Save Load Bone Caches
        if boneTools.EditCaches:
            cache_opp_row = layout.row()
            cache_opp_row.prop(boneTools, "AutoSaveBoneCaches", icon="FILE_REFRESH")
            cache_opp_row.prop(boneTools, "DeleteCachesMode", icon="TRASH")
            if not boneTools.AutoSaveBoneCaches:
                save_load_row = layout.row()
                if bones_cached:
                    save_load_row.operator("leet.cached_bones_save_disk", icon="FILE_BLANK", text="Save Caches")
                save_load_row.operator("leet.cached_bones_load_disk", icon="FILE_FOLDER", text="Load Caches")

        # Save New Cahced Selection
        if boneTools.EditCaches:
            if bones_selected:
                layout.prop(boneTools, "NewCacheName")
                if boneTools.NewCacheName == "":
                    layout.label(text="Set a name before caching bones.")
                else:
                    layout.operator("leet.sel_bones_cache", icon="BONE_DATA")
            else:
                layout.label(text="Select bone(s) to make a new cached selection.")

        layout.separator()

        # ------------------------------------------------------------------------
        #    Cursor To Bone and Back ( One bone only! )
        # ------------------------------------------------------------------------

        # When one bone is selected show the snap to cursor/snap bone to cursor tools.
        if num_bones_selected == 1:
            snap_row = layout.row()
            snap_row.operator("view3d.snap_cursor_to_selected")
            snap_row.operator("view3d.snap_selected_to_cursor")


# ------------------------------------------------------------------------
#    3D View Pie Menu - Press ctrl in pose mode to view.
# ------------------------------------------------------------------------

class VIEW3D_MT_LeetBoneOppsEffectMenu(Menu):
    bl_label = "Leet Bone Opps Effect"
    bl_idname = "VIEW3D_MT_LeetBoneOppsEffectMenu"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        layout.prop(boneTools, "EffectLoc")
        layout.prop(boneTools, "EffectRot")
        layout.prop(boneTools, "EffectScale")
        layout.separator()
        layout.label(text="These Bone Keying Tools Effect...")


class VIEW3D_MT_LeetPieMenuShowTools(Menu):
    bl_label = "Leet Pie Menu Show Tools"
    bl_idname = "VIEW3D_MT_LeetPieMenuShowTools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings

        layout.prop(boneTools, "ViewPieFrameKeying")
        layout.prop(boneTools, "ViewPieCursorSnapTools")
        layout.separator()
        layout.label(text="Tools to show in this pie menu")


class VIEW3D_MT_PIE_LeetBonePie(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Leet Bone Tools"
    bl_idname = "VIEW3D_MT_PIE_LeetBonePie"

    @classmethod
    def poll(self, context):
        # Only show panel when an armature is selected.
        if context.object is not None:
            return context.object.type == 'ARMATURE'
        return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        boneTools = scene.leetBoneToolsSettings
        currArm = bpy.context.object.name

        # currArm = bpy.context.object.name
        num_bones_selected = len(bpy.context.selected_pose_bones)
        bones_selected = num_bones_selected > 0
        bones_cached = len(boneTools.CachedSelections[currArm]) > 0

        pie = layout.menu_pie()

        # Tool Setting Box
        boneOps = pie.column().box()
        boneOps.label(text="Tools Settings", icon="TOOL_SETTINGS")

        if bones_cached:

            # Show the bone selection tools
            boneOps.prop(boneTools, "ReplaceSelected", icon="SELECT_SET")
            boneOps.prop(boneTools, "FocusOnSelected", icon="ZOOM_SELECTED")

            if boneTools.ViewPieTools:
                cachesStack = pie.column()
                cacheView = cachesStack.box()
                cacheView.label(text="Replace Selection" if boneTools.ReplaceSelected else "Add To Selection")

            # List all of the bone groups for this arm with the targeted action
            for i in boneTools.CachesOrder[currArm]:
                # Naming of group
                size = len(boneTools.CachedSelections[currArm][i])
                b = "Bones" if size > 1 else "Bone"
                ico = "SELECT_SET" if boneTools.ReplaceSelected else "SELECT_EXTEND"

                # Add cache to select
                if boneTools.ViewPieTools:
                    op = cacheView.operator("leet.cached_bones_sel", text="{} ({} {})".format(i, size, b),
                                            icon=ico)
                    op.sel_group = i

                else:
                    op = pie.operator("leet.cached_bones_sel", text="{} ({} {})".format(i, size, b), icon=ico)
                    op.sel_group = i

        else:
            # Option to load the bones
            load = pie.column().box()
            load.label(text="No selection cached for {}".format(currArm))
            load.operator("leet.cached_bones_load_disk", icon="FILE_FOLDER")

        # Show Hide Other Bone Tools Setting
        boneOps.prop(boneTools, "ViewPieTools")

        if boneTools.ViewPieTools:
            # Show which tools can be toggled to show on the pie menu or not.
            boneOps.menu('VIEW3D_MT_LeetPieMenuShowTools', icon='RIGHTARROW_THIN', text='Show Tools...')

            # ------------------------------------------------------------------------
            #    Move bone and Keying Opps
            # ------------------------------------------------------------------------
            if bones_selected and boneTools.ViewPieFrameKeying:
                other = pie.column()
                other_menu = other.box().column()
                other_menu.scale_y = 1.3
                other_menu.label(text="Affect {} Selected Bones".format(num_bones_selected))
                other_menu.operator("leet.key_bones", icon="KEYTYPE_KEYFRAME_VEC")
                other_menu.operator("leet.clear_key_bones", icon="TRASH")
                other_menu.operator("leet.reset_bones", icon="FILE_REFRESH")
                other_menu.menu('VIEW3D_MT_LeetBoneOppsEffectMenu', icon='RIGHTARROW_THIN', text='Opps Effect...')

            # ------------------------------------------------------------------------
            #    Cursor To Bone and Back ( One bone only! )
            # ------------------------------------------------------------------------
            if num_bones_selected == 1 and boneTools.ViewPieCursorSnapTools:
                # When one bone is selected show the snap to cursor/snap bone to cursor tools.
                snap_box = pie.box().column()
                snap_box.operator("view3d.snap_cursor_to_selected")
                snap_box.operator("view3d.snap_selected_to_cursor")


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    LeetBoneToolsSettings,
    OBJECT_PT_LeetBonePanel,
    VIEW3D_MT_LeetBoneOppsEffectMenu,
    VIEW3D_MT_PIE_LeetBonePie,
    VIEW3D_MT_LeetPieMenuShowTools,
    Leet_CacheBonesLoadDisk,
    Leet_CacheBonesSaveDisk,
    Leet_CacheSelectedBones,
    Leet_CachedBoneMoveIndex,
    Leet_SelectCachedBonesSet,
    Leet_DeleteCachedBonesSet,
    Leet_ResetBones,
    Leet_KeyBones,
    Leet_ClearKeyBones,
)

addon_keymaps = []


def register():
    # Register Classes
    for cls in classes:
        register_class(cls)

    # Register Bone Tools Settings
    bpy.types.Scene.leetBoneToolsSettings = PointerProperty(type=LeetBoneToolsSettings)

    # Handle the key mapping
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Pose')
    # km = wm.keyconfigs.addon.keymaps.new(name='Armature', space_type='EMPTY', region_type='WINDOW')
    kmi = km.keymap_items.new("wm.call_menu_pie", "LEFTMOUSE", "PRESS",
                              ctrl=True).properties.name = "VIEW3D_MT_PIE_LeetBonePie"
    addon_keymaps.append(km)


def unregister():
    # Unregister the classes
    for cls in reversed(classes):
        unregister_class(cls)

    # Delete the scene settings
    del bpy.types.Scene.leetBoneToolsSettings

    # Handle the key mapping
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
