#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id:ReorderIds.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Change id IDs of all the elements in the database to conform to the
scheme specified in the database's prefix ids
"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import re
from gettext import gettext as _

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gui.utils import ProgressMeter
import gen.lib
from PluginUtils import Tool
from gen.plug import PluginManager

_findint = re.compile('^[^\d]*(\d+)[^\d]*')

#-------------------------------------------------------------------------
#
# Actual tool
#
#-------------------------------------------------------------------------
class ReorderIds(Tool.BatchTool):
    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        Tool.BatchTool.__init__(self, dbstate, options_class, name)
        if self.fail:
            return

        db = dbstate.db
        self.uistate = uistate
        if uistate:
            self.progress = ProgressMeter(_('Reordering GRAMPS IDs'),'')
        else:
            print "Reordering GRAMPS IDs..."

        self.trans = db.transaction_begin("", batch=True)
        db.disable_signals()

        if uistate:
            self.progress.set_pass(_('Reordering People IDs'),
                                   db.get_number_of_people())
        self.reorder(gen.lib.Person,
                     db.get_person_from_gramps_id,
                     db.get_person_from_handle,
                     db.find_next_person_gramps_id,
                     db.person_map,
                     db.commit_person,
                     db.person_prefix)

        if uistate:
            self.progress.set_pass(_('Reordering Family IDs'),
                                   db.get_number_of_families())
        self.reorder(gen.lib.Family,
                     db.get_family_from_gramps_id,
                     db.get_family_from_handle,
                     db.find_next_family_gramps_id,
                     db.family_map,
                     db.commit_family,
                     db.family_prefix)
        if uistate:
            self.progress.set_pass(_('Reordering Event IDs'),
                                   db.get_number_of_events())
        self.reorder(gen.lib.Event,
                     db.get_event_from_gramps_id,
                     db.get_event_from_handle,
                     db.find_next_event_gramps_id,
                     db.event_map,
                     db.commit_event,
                     db.event_prefix)
        if uistate:
            self.progress.set_pass(_('Reordering Media Object IDs'),
                                   db.get_number_of_media_objects())
        self.reorder(gen.lib.MediaObject,
                     db.get_object_from_gramps_id,
                     db.get_object_from_handle,
                     db.find_next_object_gramps_id,
                     db.media_map,
                     db.commit_media_object,
                     db.mediaobject_prefix)
        if uistate:
            self.progress.set_pass(_('Reordering Source IDs'),
                                   db.get_number_of_sources())
        self.reorder(gen.lib.Source,
                     db.get_source_from_gramps_id,
                     db.get_source_from_handle,
                     db.find_next_source_gramps_id,
                     db.source_map,
                     db.commit_source,
                     db.source_prefix)
        if uistate:
            self.progress.set_pass(_('Reordering Place IDs'),
                                   db.get_number_of_places())
        self.reorder(gen.lib.Place,
                     db.get_place_from_gramps_id,
                     db.get_place_from_handle,
                     db.find_next_place_gramps_id,
                     db.place_map,
                     db.commit_place,
                     db.place_prefix)
        if uistate:
            self.progress.set_pass(_('Reordering Repository IDs'),
                                   db.get_number_of_repositories())
        self.reorder(gen.lib.Repository,
                     db.get_repository_from_gramps_id,
                     db.get_repository_from_handle,
                     db.find_next_repository_gramps_id,
                     db.repository_map,
                     db.commit_repository,
                     db.repository_prefix)
#add reorder notes ID
        if uistate:
            self.progress.set_pass(_('Reordering Note IDs'),
                                   db.get_number_of_notes())
        self.reorder(gen.lib.Note,
                     db.get_note_from_gramps_id,
                     db.get_note_from_handle,
                     db.find_next_note_gramps_id,
                     db.note_map,
                     db.commit_note,
                     db.note_prefix)
        if uistate:
            self.progress.close()
        else:
            print "Done."

        db.transaction_commit(self.trans, _("Reorder GRAMPS IDs"))
        db.enable_signals()
        db.request_rebuild()
        
    def reorder(self, class_type, find_from_id, find_from_handle,
                find_next_id, table, commit, prefix):
        dups = []
        newids = {}

        for handle in table.keys():
            if self.uistate:
                self.progress.step()

            sdata = table[handle]

            obj = class_type()
            obj.unserialize(sdata)
            gramps_id = obj.get_gramps_id()
            # attempt to extract integer, if we can't, treat it as a
            # duplicate

            match = _findint.match(gramps_id)
            if match:
                # get the integer, build the new handle. Make sure it
                # hasn't already been chosen. If it has, put this
                # in the duplicate handle list

                try:
                    index = match.groups()[0]
                    newgramps_id = prefix % int(index)
                    if newgramps_id == gramps_id:
                        newids[newgramps_id] = gramps_id
                    elif find_from_id(newgramps_id) is not None:
                        dups.append(obj.get_handle())
                    else:
                        obj.set_gramps_id(newgramps_id)
                        commit(obj, self.trans)
                        newids[newgramps_id] = gramps_id
                except:
                    dups.append(handle)
            else:
                dups.append(handle)

        # go through the duplicates, looking for the first available
        # handle that matches the new scheme.
    
        if self.uistate:
            self.progress.set_pass(_('Finding and assigning unused IDs'),
                                   len(dups))
        for handle in dups:
            if self.uistate:
                self.progress.step()
            obj = find_from_handle(handle)
            obj.set_gramps_id(find_next_id())
            commit(obj, self.trans)
    
#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class ReorderIdsOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, person_id=None):
        Tool.ToolOptions.__init__(self, name, person_id)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
pmgr = PluginManager.get_instance()
pmgr.register_tool(
    name = 'reorder_ids',
    category = Tool.TOOL_DBPROC,
    tool_class = ReorderIds,
    options_class = ReorderIdsOptions,
    modes = PluginManager.TOOL_MODE_GUI | PluginManager.TOOL_MODE_CLI,
    translated_name = _("Reorder GRAMPS IDs"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description = _("Reorders the gramps IDs "
                    "according to Gramps' default rules.")
    )
