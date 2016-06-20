/**
 * @license Copyright (c) 2003-2015, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */
CKEDITOR.editorConfig = function( config ) {
	config.entities_latin = false;
  config.entities_greek = false;
  config.entities = false;
  config.basicEntities = false;
	config.height = '800px';
	config.toolbarGroups = [
		{ name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
		{ name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
		{ name: 'forms', groups: [ 'forms' ] },
		{ name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi', 'paragraph' ] },
		{ name: 'links', groups: [ 'links' ] },
		{ name: 'editing', groups: [ 'find', 'selection', 'spellchecker', 'editing' ] },
		{ name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
		{ name: 'tools', groups: [ 'tools' ] },
		{ name: 'insert', groups: [ 'insert' ] },
		{ name: 'colors', groups: [ 'colors' ] },
		{ name: 'styles', groups: [ 'styles' ] },
		{ name: 'others', groups: [ 'others' ] },
		{ name: 'about', groups: [ 'about' ] }
	];

	config.removeButtons = 'Print,NewPage,Save,Templates,Cut,Copy,Paste,PasteText,PasteFromWord,Undo,Redo,Find,SelectAll,Radio,Checkbox,TextField,Textarea,Select,Button,ImageButton,HiddenField,Form,RemoveFormat,CreateDiv,Anchor,Flash,PageBreak,ShowBlocks,About';
};
