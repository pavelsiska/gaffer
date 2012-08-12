##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#  
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#  
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

import os
import re

import IECore

import Gaffer
import GafferUI

class PresetDialogue( GafferUI.Dialogue ) :

	def __init__( self, title, parameterHandler ) :
	
		GafferUI.Dialogue.__init__( self, title )
		
		self._parameterHandler = parameterHandler

	def _locationMenu( self, **kw ) :
	
		menu = GafferUI.SelectionMenu( **kw )
		for searchPath in self._searchPaths() :
			menu.addItem( searchPath )
		
		return menu

	def _searchPaths( self ) :
	
		parameterised = self._parameterHandler.plug().node().getParameterised()
		searchPathEnvVar = parameterised[3]
		if not searchPathEnvVar :
			# we need to guess based on type
			if isinstance( parameterised[0], IECore.Op ) :
				searchPathEnvVar = "IECORE_OP_PATHS"
			elif isinstance( parameterised[0], IECore.ParameterisedProcedural ) :
				searchPathEnvVar = "IECORE_PROCEDURAL_PATHS"
			else :
				raise Exception( "Unable to determine save location for presets" )		
		
		searchPathEnvVar = searchPathEnvVar.replace( "_PATHS", "_PRESET_PATHS" )
		paths = os.environ[searchPathEnvVar].split( ":" )
		
		existingPaths = []
		for path in paths :
			if not os.path.isdir( path ) :
				with IECore.IgnoredExceptions( Exception ) :
					os.makedirs( path )
			if os.path.isdir( path ) :
				existingPaths.append( path )
				
		return existingPaths

class SavePresetDialogue( PresetDialogue ) :

	def __init__( self, parameterHandler ) :
	
		PresetDialogue.__init__( self, "Save Preset", parameterHandler )
				
		with GafferUI.ListContainer( spacing = 8 ) as column :
			with GafferUI.GridContainer( spacing = 6 ) :
				
				GafferUI.Label(
					"<h3>Location</h3>",
					index = ( 0, 0 ),
					alignment = (
						GafferUI.Label.HorizontalAlignment.Right,
						GafferUI.Label.VerticalAlignment.None,
					),
				)
				self.__locationMenu = self._locationMenu( index = ( 1, 0 ) )
				
				GafferUI.Label(
					"<h3>Name</h3>",
					index = ( 0, 1 ),
					alignment = (
						GafferUI.Label.HorizontalAlignment.Right,
						GafferUI.Label.VerticalAlignment.None,
					),
				)
				self.__presetNameWidget = GafferUI.TextWidget( "Enter a name!", index = ( 1, 1 ) )
				self.__presetNameWidget.setSelection( None, None ) # select all
				self.__presetNameChangedConnection = self.__presetNameWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__updateSaveButton ) )
						
				GafferUI.Label(
					"<h3>Description</h3>",
					index = ( 0, 2 ),
					alignment = (
						GafferUI.Label.HorizontalAlignment.Right,
						GafferUI.Label.VerticalAlignment.Top,
					),
				)
				
				self.__presetDescriptionWidget = GafferUI.MultiLineTextWidget( index = ( 1, 2 ), )
				self.__presetDescriptionChangedConnection = self.__presetDescriptionWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__updateSaveButton ) )
		
			with GafferUI.Collapsible( "Parameters To Save", collapsed=True ) as cl :
			
				parameterPath = Gaffer.DictPath( parameterHandler.parameter(), "/", dictTypes = ( dict, IECore.CompoundData, IECore.CompoundObject, IECore.CompoundParameter ) )
				self.__parameterListing = GafferUI.PathListingWidget(
					parameterPath,
					columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
					allowMultipleSelection = True,
					displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
				)
				self.__parameterListing.setSelectedPaths( self.__allPaths( parameterPath ) )
				self.__haveSelectedParameters = True
				self.__selectionChangedConnection = self.__parameterListing.selectionChangedSignal().connect(
					Gaffer.WeakMethod( self.__selectionChanged )
				)
						
		self._setWidget( column )
		
		self._addButton( "Cancel" )
		self.__saveButton = self._addButton( "Save" )
		self.__saveButton.setEnabled( False )

	def waitForSave( self, **kw ) :
	
		self.__presetNameWidget.grabFocus()
			
		while 1 :
		
			button = self.waitForButton( **kw )
			if button is self.__saveButton :
				if self.__save() :
					return True
			else :
				return False
							
	def __save( self ) :
	
		self._parameterHandler.setParameterValue()
		parameterised = self._parameterHandler.plug().node().getParameterised()[0]
		preset = IECore.BasicPreset(
			parameterised,
			self._parameterHandler.parameter(),
			self.__selectedParameters()
		)
		
		presetLocation = self.__locationMenu.getCurrentItem()
		presetDescription = self.__presetDescriptionWidget.getText()
		
		presetName = self.__presetNameWidget.getText()
		# make a filename by sanitising the preset name.
		fileName = presetName.replace( " ", "_" )
		fileName = re.sub( '[^a-zA-Z0-9_]*', "", fileName )
		# We have to also make sure that the name doesn't begin with a number,
		# as it wouldn't be a legal class name in the resulting py stub.
		fileName = re.sub( '^[0-9]+', "", fileName )
		
		preset.save( presetLocation, fileName, presetName, presetDescription )
		
		return True
		
	def __allPaths( self, path ) :
	
		result = [ path ]
		if not path.isLeaf() :
			for childPath in path.children() :
				result.extend( self.__allPaths( childPath ) )
				
		return result
	
	def __updateSaveButton( self, *unused ) :
	
		enabled = True
		
		presetName = self.__presetNameWidget.getText()
		if not presetName or presetName == "Enter a name!" :
			enabled = False
			
		if not self.__presetDescriptionWidget.getText() :
			enabled = False
			
		if not self.__haveSelectedParameters :
			enabled = False
		
		self.__saveButton.setEnabled( enabled )
		
	def __selectedParameters( self ) :
	
		result = []
		selectedPaths = self.__parameterListing.getSelectedPaths()
		for path in selectedPaths :
			info = path.info()
			parameter = info.get( "dict:value", None )
			if parameter is not None :
				result.append( parameter )
						
		return result
				
	def __selectionChanged( self, pathListing ) :

		self.__haveSelectedParameters = bool( self.__selectedParameters() )
		self.__updateSaveButton()
		
class LoadPresetDialogue( PresetDialogue ) :

	def __init__( self, parameterHandler ) :
	
		PresetDialogue.__init__( self, "Load Preset", parameterHandler )
		
		with GafferUI.SplitContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as row :
			
			with GafferUI.ListContainer( spacing=4 ) :
			
				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				
					GafferUI.Label(
						"<h3>Location</h3>",
						horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
					)
					self.__locationMenu = self._locationMenu()
					self.__locationMenuChangedConnection = self.__locationMenu.currentIndexChangedSignal().connect( Gaffer.WeakMethod( self.__locationChanged ) )
				
				self.__presetListing = GafferUI.PathListingWidget(
					Gaffer.DictPath( {}, "/" ),
					columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
					displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
				)
				self.__selectionChangedConnection = self.__presetListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
			
			with GafferUI.ListContainer( spacing=4 ) :
				self.__presetDetailsLabel = GafferUI.Label( "<h3>Description</h3>" )
				self.__presetDetailsWidget = GafferUI.MultiLineTextWidget( editable = False )
				
		self._setWidget( row )
		
		self._addButton( "Cancel" )
		self.__loadButton = self._addButton( "Load" )
		self.__loadButton.setEnabled( False )
		
		self.__updatePresetListing()
		
		row.setSizes( [ 0.5, 0.5 ] )
		
	def waitForLoad( self, **kw ) :
	
		button = self.waitForButton( **kw )
		if button is self.__loadButton :
			self.__load()
			return True
			
		return False

	def __load( self ) :
	
		preset = self.__selectedPreset()
		assert( preset is not None )
		
		node = self._parameterHandler.plug().node()
		parameterised = node.getParameterised()[0]
		with node.parameterModificationContext() :
			preset( parameterised, self._parameterHandler.parameter() )
			
	def __locationChanged( self, locationMenu ) :
	
		self.__updatePresetListing()
		
	def __updatePresetListing( self ) :
	
		location = self.__locationMenu.getCurrentItem()
		presetLoader = IECore.ClassLoader( IECore.SearchPath( location, ":" ) )
		parameterised = self._parameterHandler.plug().node().getParameterised()[0]
		
		d = {}
		for presetName in presetLoader.classNames() :
			preset = presetLoader.load( presetName )()
			if preset.applicableTo( parameterised, self._parameterHandler.parameter() ) :
				d[preset.metadata()["title"]] = preset

		self.__presetListing.setPath( Gaffer.DictPath( d, "/" ) )
		self.__selectionChanged()

	def __selectedPreset( self ) :
	
		selection = self.__presetListing.getSelectedPaths()
		if not selection :
			return None
			
		return selection[0].info()["dict:value"]	

	def __selectionChanged( self, *unused ) :
	
		preset = self.__selectedPreset()
		if preset is None :
			loadEnabled = False
			text = "No preset selected"			
		else :
			loadEnabled = True
			text = preset.metadata()["description"]
			if not text.strip() :
				text = "No description provided"
			
		self.__presetDetailsWidget.setText( text )
		self.__loadButton.setEnabled( loadEnabled )
		
##########################################################################
# Plumbing to make the dialogues available from parameter menus.
##########################################################################
		
def __loadPreset( parameterHandler ) :

	dialogue = LoadPresetDialogue( parameterHandler )
	dialogue.waitForLoad()

def __savePreset( parameterHandler ) :

	dialogue = SavePresetDialogue( parameterHandler )
	dialogue.waitForSave()
	# \todo We should be giving the window a parent, but we can't
	# because GafferUI.Menu won't pass the menu argument to commands
	# which are curried functions.
	
def __parameterPopupMenu( menuDefinition, parameterHandler ) :

	if not parameterHandler.isSame( parameterHandler.plug().node().parameterHandler() ) :
		# only apply ourselves to the top level parameter for now
		return
		
	menuDefinition.append( "/PresetsDivider", { "divider" : True } )
	menuDefinition.append( "/Save Preset...", { "command" : IECore.curry( __savePreset, parameterHandler ) } )
	menuDefinition.append( "/Load Preset...", { "command" : IECore.curry( __loadPreset, parameterHandler ) } )
	
__popupMenuConnection = GafferUI.ParameterValueWidget.popupMenuSignal().connect( __parameterPopupMenu )