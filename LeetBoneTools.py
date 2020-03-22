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
    NumCachePerRow: IntProperty(
        name="Caches Per Row",
        description="The number of caches to show on a single row",
        default=1,
        min=1,
        max=4
    )

    NumCachePerRowPie: IntProperty(
        name="Pie Caches Per Row",
        description="The number of caches to show on a single row in the pie menu",
        default=1,
        min=1,
        max=3
    )

    CompactKeyingTool: BoolProperty(
        name="Use Compact Bone Keying Tool",
        description="This will force the keying tool to appear be compact.",
        default=True
    )

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

    UseDirectorySaves: BoolProperty(
        name="Use Directory Saves",
        description="When true bone caches will be used by all blend files within this shared save directory instead "
                    "of being saved per blend file",
        default=True
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
        name="View Tools In Pie Menu",
        description="This will show leet bone tools in the pie menu, and make the cache list a list",
        default=True
    )

    ViewFrameKeying: BoolProperty(
        name="Bone Keying Tools",
        description="This will show the current frame bone keying tools in the pie menu",
        default=True
    )

    ViewCursorSnapTools: BoolProperty(
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

def GetCWDAndFileName(share_setting_with_folder: bool = False):
    """
    This will return the folder and directory where the bone selections are saved.
    :param share_setting_with_folder: If true the saved set of selections will be loadable by all
            blend files in this directory.
    :return: Tuple of the folder where this file is saved, and the name of the txt file holding the saved info.
    """
    # Returns the current cwd, and file name
    cwd, file_name = ntSplit(bpy.data.filepath)
    if share_setting_with_folder:
        file_name = "LeetBoneToolsSelections_FolderShared.txt"
    else:
        file_name = file_name.strip(".blend") + "-LeetBoneToolsSelections.txt"
    return cwd, file_name


# ------------------------------------------------------------------------
#    Operators - Cached Bone Selections / Saving / Loading
# ------------------------------------------------------------------------

class Leet_CacheBonesLoadDisk(Operator):
    bl_label = "Load Cached Bones From Disk"
    bl_idname = "leet.cached_bones_load_disk"

    def execute(self, context):
        scene = context.scene
        bone_tools = scene.leetBoneToolsSettings

        # Saves the current matches to a file so they can be loaded.
        # bone_tools.AttemptedLoadBoneCache = True
        cwd, fileName = GetCWDAndFileName(bone_tools.UseDirectorySaves)
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
        cwd, fileName = GetCWDAndFileName(boneTools.UseDirectorySaves)
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
        bone_tools = scene.leetBoneToolsSettings

        # Save Arm Name
        bone_tools.CurrArm = bpy.context.object.name
        newGroup = bone_tools.NewCacheName

        # Cache the selected bones
        if len(bpy.context.selected_pose_bones) > 0:

            # Add new dict item for saved group
            bone_tools.CachedSelections[bone_tools.CurrArm][newGroup] = []
            bone_tools.CachesOrder[bone_tools.CurrArm].append(newGroup)

            # Get the set of valid bones
            bones = set(bpy.data.objects[bone_tools.CurrArm].data.bones.keys())

            for i in bpy.context.selected_pose_bones:
                # Filter out bones on other armatures
                if i.name in bones:
                    bone_tools.CachedSelections[bone_tools.CurrArm][newGroup].append(i.name)

            # Save changes
            if bone_tools.AutoSaveBoneCaches:
                bpy.ops.leet.cached_bones_save_disk()

        return {'FINISHED'}


class Leet_SelectCachedBones(Operator):
    bl_label = "Select Cached Bones"
    bl_idname = "leet.cached_bones_sel"

    sel_group: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        bone_tools = scene.leetBoneToolsSettings

        # Save Arm Name
        bone_tools.CurrArm = bpy.context.object.name

        # Check valid input
        if self.sel_group == "":
            return {'FINISHED'}
        elif self.sel_group not in bone_tools.CachedSelections[bone_tools.CurrArm]:
            return {'FINISHED'}

        # Clear old selection?
        if bone_tools.ReplaceSelected:
            bpy.ops.pose.select_all(action='DESELECT')

        # Select the cached bones
        for i in bone_tools.CachedSelections[bone_tools.CurrArm][self.sel_group]:
            b = bpy.data.objects[bone_tools.CurrArm].data.bones[i]
            b.select = True

        # Should we focus on the selected objects?
        if bone_tools.FocusOnSelected:
            bpy.ops.view3d.view_selected()

        return {'FINISHED'}


class Leet_CachedBoneMoveIndex(Operator):
    bl_label = "Move Index of Cached Bones"
    bl_idname = "leet.cached_bones_move_index"

    sel_group: bpy.props.StringProperty()
    move_up: bpy.props.BoolProperty()

    def execute(self, context):
        scene = context.scene
        bone_tools = scene.leetBoneToolsSettings

        # Save Arm Name
        bone_tools.CurrArm = bpy.context.object.name

        # Get arm cache count
        c = len(bone_tools.CachesOrder[bone_tools.CurrArm])

        if self.sel_group == "":
            return {'FINISHED'}
        elif self.sel_group not in bone_tools.CachesOrder[bone_tools.CurrArm]:
            return {'FINISHED'}
        elif c <= 1:
            return {'FINISHED'}

        # Switch the index
        modVal = len(bone_tools.CachesOrder[bone_tools.CurrArm])
        sel_index = bone_tools.CachesOrder[bone_tools.CurrArm].index(self.sel_group)
        if self.move_up:
            new_index = sel_index - 1
        else:
            new_index = sel_index + 1
        sel_index = sel_index % modVal
        new_index = new_index % modVal
        bone_tools.CachesOrder[bone_tools.CurrArm][sel_index], \
        bone_tools.CachesOrder[bone_tools.CurrArm][new_index] = bone_tools.CachesOrder[bone_tools.CurrArm][new_index], \
                                                              bone_tools.CachesOrder[bone_tools.CurrArm][sel_index]

        # Save changes
        if bone_tools.AutoSaveBoneCaches:
            bpy.ops.leet.cached_bones_save_disk()

        return {'FINISHED'}


class Leet_DeleteCachedBonesSet(Operator):
    bl_label = "Delete Cached Bones"
    bl_idname = "leet.delete_cached_bones_set"

    sel_group: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        bone_tools = scene.leetBoneToolsSettings

        # Save Arm Name
        bone_tools.CurrArm = bpy.context.object.name

        if self.sel_group == "":
            return {'FINISHED'}
        elif self.sel_group not in bone_tools.CachedSelections[bone_tools.CurrArm]:
            return {'FINISHED'}

        # Delete the selection cache
        del bone_tools.CachedSelections[bone_tools.CurrArm][self.sel_group]
        ind = bone_tools.CachesOrder[bone_tools.CurrArm].index(self.sel_group)
        del bone_tools.CachesOrder[bone_tools.CurrArm][ind]

        # Save changes
        if bone_tools.AutoSaveBoneCaches:
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
        bone_tools = scene.leetBoneToolsSettings

        if bone_tools.EffectLoc:
            bpy.ops.anim.keyframe_insert_menu(type='Location')

        if bone_tools.EffectRot:
            bpy.ops.anim.keyframe_insert_menu(type='Rotation')

        if bone_tools.EffectScale:
            bpy.ops.anim.keyframe_insert_menu(type='Scaling')

        return {'FINISHED'}


class Leet_ClearKeyBones(Operator):
    bl_label = "Clear Keys"
    bl_idname = "leet.clear_key_bones"

    def execute(self, context):
        scene = context.scene

        # Set keyfranes on the selected bones
        bone_tools = scene.leetBoneToolsSettings
        f = bpy.context.scene.frame_current

        for i in bpy.context.selected_pose_bones:
            if bone_tools.EffectLoc:
                i.keyframe_delete('location', frame=f)

            if bone_tools.EffectRot:
                i.keyframe_delete('rotation_euler', frame=f)
                i.keyframe_delete('rotation_quaternion', frame=f)

            if bone_tools.EffectScale:
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
        bone_tools = scene.leetBoneToolsSettings

        # ------------------------------------------------------------------------
        #    Move bone and Keying Opps
        # ------------------------------------------------------------------------

        # Set curr arm, and add it to the selection cache dict
        currArm = bpy.context.object.name
        if currArm not in bone_tools.CachedSelections:
            bone_tools.CachedSelections[currArm] = {}
        if currArm not in bone_tools.CachesOrder:
            bone_tools.CachesOrder[currArm] = []

        # Number of bones selected
        num_bones_selected = len(bpy.context.selected_pose_bones)
        bones_selected = num_bones_selected > 0
        caches_count = len(bone_tools.CachedSelections[currArm])
        bones_cached = caches_count > 0

        # ------------------------------------------------------------------------
        #    Keyframing Tool
        # ------------------------------------------------------------------------

        if bone_tools.ViewFrameKeying:
            keying_box = layout.box()
            if bones_selected:
                bones_keying_opps_row = keying_box.box().row()
                bones_keying_opps_row.operator("leet.key_bones", icon="KEYTYPE_KEYFRAME_VEC")
                bones_keying_opps_row.operator("leet.clear_key_bones", icon="TRASH")
                bones_keying_opps_row.operator("leet.reset_bones", icon="FILE_REFRESH")

                if bone_tools.CompactKeyingTool:
                    bones_keying_opps_row.menu('VIEW3D_MT_LeetBoneOppsEffectMenu', icon='RIGHTARROW_THIN',
                                               text='Opps Effect')
                else:
                    effect_keys_row = keying_box.row()
                    effect_keys_row.prop(bone_tools, "EffectLoc")
                    effect_keys_row.prop(bone_tools, "EffectRot")
                    effect_keys_row.prop(bone_tools, "EffectScale")

            else:
                no_bones_selected_row = keying_box.row()
                no_bones_selected_row.label(text="Select bone(s) to affect keying.")
                no_bones_selected_row.menu('VIEW3D_MT_LeetBoneOppsEffectMenu', icon='RIGHTARROW_THIN',
                                           text='Opps Effect...')

        # ------------------------------------------------------------------------
        #    Caching Bone Selections
        # ------------------------------------------------------------------------

        # Cached Selection Label
        if not bones_cached:
            no_caches_box = layout.box()
            no_caches_box.label(text="No selections cached for {}".format(currArm))
            no_caches_box.operator("leet.cached_bones_load_disk", icon="FILE_FOLDER")

        if bones_cached:
            bone_sel_box = layout.box()

            n = 0
            selection_box = bone_sel_box.box()
            br = selection_box.row()

            # List all of the bone groups for this arm with the targeted action
            for i in bone_tools.CachesOrder[currArm]:

                # Make or continue cache row
                if n == bone_tools.NumCachePerRow:
                    n = 0
                    br = selection_box.row()
                n += 1

                # Naming of group
                size = len(bone_tools.CachedSelections[currArm][i])
                b = "Bones" if size > 1 else "Bone"

                if bone_tools.EditCaches:  # Delete Group
                    if bone_tools.DeleteCachesMode:
                        op = br.operator("leet.delete_cached_bones_set", icon="TRASH",
                                         text="{} ({} {})".format(i, size, b))
                        op.sel_group = i

                    else:  # Move Caches
                        moveRow = br.row()
                        moveRow.label(text="{} ({})".format(i, size))

                        if caches_count > 1:  # Buttons to move up and down
                            if bone_tools.NumCachePerRow == 1:
                                opU = moveRow.operator("leet.cached_bones_move_index", text="", icon="SORT_DESC")
                                opD = moveRow.operator("leet.cached_bones_move_index", text="", icon="SORT_ASC")
                            else:
                                opU = moveRow.operator("leet.cached_bones_move_index", text="", icon="TRIA_LEFT")
                                opD = moveRow.operator("leet.cached_bones_move_index", text="", icon="TRIA_RIGHT")
                            opU.sel_group, opD.sel_group = i, i
                            opU.move_up, opD.move_up = True, False

                else:  # Select Group
                    ico = "SELECT_SET" if bone_tools.ReplaceSelected else "SELECT_EXTEND"
                    op = br.operator("leet.cached_bones_sel", text="{} ({} {})".format(i, size, b), icon=ico)
                    op.sel_group = i

            # Button Actions Configuration
            sel_action_edit_row = bone_sel_box.row()
            sel_action_edit_row.prop(bone_tools, "ReplaceSelected", icon="SELECT_SET")
            sel_action_edit_row.prop(bone_tools, "FocusOnSelected", icon="ZOOM_SELECTED")

        # Keying Selected Bones Controls Current Frame Tools
        bo = "Bone" if num_bones_selected == 1 else "Bones"
        top_box = layout.box()
        top_row = top_box.row()
        arm_subrow = top_row.row()
        arm_subrow.label(text="{} {} Selected".format(num_bones_selected, bo))
        arm_subrow.label(text="{}".format(currArm))

        # Load or Delete Cached Selection
        top_edit_row = top_box.row()
        top_edit_row.prop(bone_tools, "EditCaches", icon="SETTINGS")
        top_edit_row.menu('VIEW3D_MT_LeetMenuShowTools', icon='VIEWZOOM', text='Show...')

        # Save Load Bone Caches
        if bone_tools.EditCaches:
            edit_add_box = layout.box()

            cache_opp_row = edit_add_box.row()
            cache_opp_row.prop(bone_tools, "AutoSaveBoneCaches", icon="FILE_REFRESH")
            cache_opp_row.prop(bone_tools, "DeleteCachesMode", icon="TRASH")

            if not bone_tools.AutoSaveBoneCaches:
                save_load_row = edit_add_box.box().row()
                if bones_cached:
                    save_load_row.operator("leet.cached_bones_save_disk", icon="FILE_BLANK", text="Save Caches")
                save_load_row.operator("leet.cached_bones_load_disk", icon="FILE_FOLDER", text="Load Caches")

            # Save New Cached Selection
            new_cache_box = edit_add_box.box()
            if bones_selected:
                new_cache_box.prop(bone_tools, "NewCacheName")
                if bone_tools.NewCacheName == "":
                    new_cache_box.label(text="Set a name before caching bones.")
                else:
                    new_cache_box.operator("leet.sel_bones_cache", icon="BONE_DATA")
            else:
                new_cache_box.label(text="Select bone(s) to make a new cached selection.")

        if bone_tools.ViewCursorSnapTools:
            # ------------------------------------------------------------------------
            #    Cursor To Bone and Back ( One bone only! )
            # ------------------------------------------------------------------------

            # When one bone is selected show the snap to cursor/snap bone to cursor tools.
            if num_bones_selected == 1:
                snap_row = layout.box().row()
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
        bone_tools = scene.leetBoneToolsSettings

        layout.prop(bone_tools, "EffectLoc")
        layout.prop(bone_tools, "EffectRot")
        layout.prop(bone_tools, "EffectScale")
        layout.separator()
        layout.label(text="These Bone Keying Tools Effect...")


class VIEW3D_MT_LeetMenuShowTools(Menu):
    bl_label = "Show Bone Tools Menu"
    bl_idname = "VIEW3D_MT_LeetMenuShowTools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bone_tools = scene.leetBoneToolsSettings

        # Display Settings
        layout.label(text="Display")
        layout.prop(bone_tools, "NumCachePerRow")
        if bone_tools.ViewFrameKeying:
            layout.prop(bone_tools, "CompactKeyingTool")

        # Tools
        layout.label(text="Show Tools")
        layout.prop(bone_tools, "ViewFrameKeying")
        layout.prop(bone_tools, "ViewCursorSnapTools")

        # Save Options
        layout.label(text="Saving Options")
        layout.prop(bone_tools, "UseDirectorySaves")
        layout.prop(bone_tools, "AutoSaveBoneCaches")


class VIEW3D_MT_LeetMenuShowToolsPie(Menu):
    bl_label = "Show Bone Tools Menu"
    bl_idname = "VIEW3D_MT_LeetMenuShowToolsPie"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bone_tools = scene.leetBoneToolsSettings

        # Display Settings
        layout.label(text="Display")
        layout.prop(bone_tools, "NumCachePerRowPie")

        # Tools
        if bone_tools.ViewPieTools:
            layout.label(text="Show Tools")
            layout.prop(bone_tools, "ViewFrameKeying")
            layout.prop(bone_tools, "ViewCursorSnapTools")

        # Save Options
        layout.label(text="Saving Options")
        layout.prop(bone_tools, "UseDirectorySaves")


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
        bone_tools = scene.leetBoneToolsSettings
        curr_arm = bpy.context.object.name

        # curr_arm = bpy.context.object.name
        num_bones_selected = len(bpy.context.selected_pose_bones)
        bones_selected = num_bones_selected > 0
        bones_cached = len(bone_tools.CachedSelections[curr_arm]) > 0

        pie = layout.menu_pie()

        # Tool Setting Box
        bone_ops_box = pie.column().box()
        bone_ops_box.label(text="Plugin Settings", icon="TOOL_SETTINGS")

        if bones_cached:

            # Show the bone selection tools
            sel_op_row = bone_ops_box.row()
            sel_op_row.prop(bone_tools, "ReplaceSelected", icon="SELECT_SET")
            sel_op_row.prop(bone_tools, "FocusOnSelected", icon="ZOOM_SELECTED")

            if bone_tools.ViewPieTools:
                caches_stack = pie.column()
                cache_view = caches_stack.box()
                cache_view.label(text="Replace Selection" if bone_tools.ReplaceSelected else "Add To Selection")

            n = 0
            if bone_tools.ViewPieTools:
                br = cache_view.row()
            else:
                br = pie.column().box()

            # List all of the bone groups for this arm with the targeted action
            for i in bone_tools.CachesOrder[curr_arm]:
                # Make or continue cache row
                if n == bone_tools.NumCachePerRowPie:
                    n = 0
                    if bone_tools.ViewPieTools:
                        br = cache_view.row()
                    else:
                        br = pie.column().box()
                n += 1

                # Generate naming and icon of the bone group
                size = len(bone_tools.CachedSelections[curr_arm][i])
                b = "Bones" if size > 1 else "Bone"
                ico = "SELECT_SET" if bone_tools.ReplaceSelected else "SELECT_EXTEND"

                # Generate the select button
                op = br.operator("leet.cached_bones_sel", text="{} ({} {})".format(i, size, b),
                                 icon=ico)
                op.sel_group = i

        else:
            # Option to load the bones
            load = pie.column().box()
            load.label(text="No selection cached for {}".format(curr_arm))
            load.operator("leet.cached_bones_load_disk", icon="FILE_FOLDER")

        # Show Hide Other Bone Tools Setting
        view_row = bone_ops_box.row()
        view_row.prop(bone_tools, "ViewPieTools")
        view_row.menu('VIEW3D_MT_LeetMenuShowToolsPie', icon='VIEWZOOM', text='Show/Settings')

        if bone_tools.ViewPieTools:
            # Show which tools can be toggled to show on the pie menu or not.

            # ------------------------------------------------------------------------
            #    Move bone and Keying Opps
            # ------------------------------------------------------------------------
            if bones_selected and bone_tools.ViewFrameKeying:
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
            if num_bones_selected == 1 and bone_tools.ViewCursorSnapTools:
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
    VIEW3D_MT_LeetMenuShowToolsPie,
    VIEW3D_MT_LeetMenuShowTools,
    Leet_CacheBonesLoadDisk,
    Leet_CacheBonesSaveDisk,
    Leet_CacheSelectedBones,
    Leet_CachedBoneMoveIndex,
    Leet_SelectCachedBones,
    Leet_DeleteCachedBonesSet,
    Leet_ResetBones,
    Leet_KeyBones,
    Leet_ClearKeyBones,
)

addon_keymaps = []


def register():
    # Register Classes
    print("--------")
    for cls in classes:
        register_class(cls)

    # Register Bone Tools Settings
    bpy.types.Scene.leetBoneToolsSettings = PointerProperty(type=LeetBoneToolsSettings)

    # Handle the key mapping
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Pose')
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