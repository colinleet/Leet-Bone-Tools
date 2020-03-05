# Leet-Bone-Tools
This blender 2.8 add-on is meant to making animating sets of bones on a character faster and easier.
This tool's primary use is to make saved (cached) selections of bones on a per armature basis.
It also contains some tools to add, delete, and reset key-frames for selected bones on the current frame.

This tool-set's panel and pie menu shows-up only when an armature is selected in pose mode:
the tool-set's panel is under 3D View -> Item, and to use the pie menu hold control and left click in a 3d View.

Cached bone selections are created, edited, and deleted only in the tool's 3d-view panel, not in the pie menu.
Cached bone selections are saved in an auxiliary text file in the same directory as the blend file.
The user can choose to add to, or replace, their current selection with cached bone selections.
The user can also choose to focus on the selected bones when using the tool modify bone selections.
