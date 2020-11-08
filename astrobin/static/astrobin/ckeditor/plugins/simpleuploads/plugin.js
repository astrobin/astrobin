/**
 * @file SimpleUploads plugin for CKEditor
 *	Version: 4.5.3
 *	Uploads pasted images and files inside the editor to the server for Firefox and Chrome
 *	Feature introduced in: https://bugzilla.mozilla.org/show_bug.cgi?id=490879
 *		doesn't include images inside HTML (paste from word). IE11 does.
				https://bugzilla.mozilla.org/show_bug.cgi?id=665341

 * Includes Drag&Drop file uploads for all the new browsers.
 * Two toolbar buttons to perform quick upload of files.
 * Copyright (C) 2012-17 Alfonso Martínez de Lizarrondo

improvements: allow d&d between 2 editors in Firefox
https://bugzilla.mozilla.org/show_bug.cgi?id=454832

*/
/* globals CKEDITOR, ArrayBuffer, Uint8Array */

(function () {
	'use strict';

	// Default input element name for CSRF protection token.
	var TOKEN_INPUT_NAME = 'ckCsrfToken';

	// Wrapper to use window.alert or editor.showNotification if CKEditor supports it
	function showMessage(editor, msg) {
		// argh http://dev.ckeditor.com/ticket/13862
		var dialog = CKEDITOR.dialog.getCurrent();
		if (!dialog && editor.showNotification && editor.plugins.notification) {
			editor.showNotification(msg.replace(/\r\n/, '<br>'), 'warning');
		} else {
			alert(msg); // eslint-disable-line no-alert
		}
	}

	// If the selected image is a bmp converts it to a png
	function convertFromBmp(ev) {
		convertFromExtension(ev, /\.bmp$/);
	}

	// If the selected image is a tiff converts it to a png
	function convertFromTiff(ev) {
		convertFromExtension(ev, /\.tiff$/);
	}

	// Based on a regexp for the extension, checks if the image matches that type and converts to png
	function convertFromExtension(ev, check) {
		var data = ev.data;

		if (!check.test(data.name)) {
			return;
		}

		var img = data.image;
		var canvas = document.createElement('canvas');
		var ctx = canvas.getContext('2d');

		canvas.width = img.width;
		canvas.height = img.height;

		ctx.drawImage(img, 0, 0);

		data.file = canvas.toDataURL('image/png');
		data.name = data.name.replace(check, '.png');
	}

	//	Verifies if the selected image is within the allowed dimensions
	function checkDimension(ev) {
		var data = ev.data;
		var editor = ev.editor;
		var config = editor.config;
		var maximum = config.simpleuploads_maximumDimensions;
		var img = data.image;

		if (maximum.width && img.width > maximum.width) {
			showMessage(editor, editor.lang.simpleuploads.imageTooWide);
			ev.cancel();
			return;
		}

		if (maximum.height && img.height > maximum.height) {
			showMessage(editor, editor.lang.simpleuploads.imageTooTall);
			ev.cancel();
			return;
		}
	}

	// Custom rule similar to the fake Object to avoid generating anything if the user tries to do something strange while a file is being uploaded
	var htmlFilterRules = {
		elements: {
			$: function (element) {
				var attributes = element.attributes;
				var className = attributes && attributes['class']; // eslint-disable-line dot-notation

				// remove our wrappers
				if (className == 'simpleuploads-tmpwrapper') {
					return false;
				}
			}
		}
	};

	// CSS that we add to the editor for our internal styling
	function getEditorCss(config) {
		var imgUpload = 'span.simpleuploads-tmpwrapper>span { top: 50%; margin-top: -0.5em; width: 100%; text-align: center; color: #fff; ' +
			'text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5); font-size: 50px; font-family: Calibri,Arial,Sans-serif; pointer-events: none; ' +
			'position: absolute; display: inline-block;} \r\n';
		if (config.simpleuploads_hideImageProgress) {
			imgUpload = 'span.simpleuploads-tmpwrapper { color:#333; background-color:#fff; padding:4px; border:1px solid #EEE;} \r\n';
		}

		return '\r\n .simpleuploads-overeditor { ' + (config.simpleuploads_editorover || 'box-shadow: 0 0 10px 1px #999999 inset !important;') + ' } \r\n' +
			'a.simpleuploads-tmpwrapper { color:#333; background-color:#fff; padding:4px; border:1px solid #EEE;} \r\n' +
			'.simpleuploads-tmpwrapper { display: inline-block; position: relative; pointer-events: none;} \r\n' +
			imgUpload +
			'.simpleuploads-uploadrect {display: inline-block;height: 0.9em;vertical-align: middle;width: 20px;} \r\n' +
			'.simpleuploads-uploadrect span {background-color: #999;display: inline-block;height: 100%;vertical-align: top;} \r\n' +
			'.simpleuploads-tmpwrapper .simpleuploads-uploadcancel { background-color: #333333;border-radius: 0.5em;color: #FFFFFF;cursor: pointer !important;' +
				'display: inline-block;height: 1em;line-height: 0.8em;margin-left: 4px;padding-left: 0.18em;pointer-events: auto;' +
				'position: relative; text-decoration:none; top: -2px;width: 0.7em;} \r\n' +
			'.simpleuploads-tmpwrapper span .simpleuploads-uploadcancel { width:1em; padding-left:0} \r\n';
	}

	// Starts an upload from the data extracted from the HTML pasted
	function generateUploadFromInlinePaste(editor, imgData, type) {
		var id = CKEDITOR.plugins.simpleuploads.getTimeStampId();
		var fileName = id + '.' + type;
		var uploadData = {
			context: 'pastedimage',
			name: fileName,
			id: id,
			forceLink: false,
			file: imgData,
			mode: {type: 'base64paste'}
		};

		if (!uploadFile(editor, uploadData)) {
			return uploadData.result;
		}

		var animation = uploadData.element;
		var content = animation.$.innerHTML;
		animation.$.innerHTML = '&nbsp;';

		// only once
		editor.on('afterPaste', function (ev) {
			ev.removeListener();

			var span = editor.document.$.getElementById(id);
			if (!span) {
				return;
			}

			// fight against ACF in v4.1 and IE11, insert svg afterwards
			span.innerHTML = content;
			setupCancelButton(editor, uploadData);
			// Just in case...
			processFinishedUpload(uploadData);
		});

		return animation.getOuterHtml();
	}

	var filePicker;
	var filePickerEditor;
	var filePickerForceLink;

	function pickAndSendFile(editor, forImage, caller, callback) {
		filePickerForceLink = !forImage;
		filePickerEditor = editor;

		if (!filePicker) {
			filePicker = document.createElement('input');
			filePicker.type = 'file';
			filePicker.style.overflow = 'hidden';
			filePicker.style.width = '1px';
			filePicker.style.height = '1px';
			filePicker.style.opacity = 0.1;
			filePicker.multiple = 'multiple';

			// to trick jQueryUI
			filePicker.position = 'absolute';
			filePicker.zIndex = 1000;

			document.body.appendChild(filePicker);
			filePicker.addEventListener('change', function () {
				var count = filePicker.files.length;
				if (!count) {
					return;
				}

				// Create Undo image
				filePickerEditor.fire('saveSnapshot');

				for (var i = 0; i < count; i++) {
					var file = filePicker.files[i];
					var evData = CKEDITOR.tools.extend({}, filePicker.simpleUploadData);

					evData.file = file;
					evData.name = file.name;
					evData.originalName = evData.name;	// The original file name, to identify the upload if the name is changed afterwards

					evData.id = CKEDITOR.plugins.simpleuploads.getTimeStampId();
					evData.forceLink = filePickerForceLink;
					evData.mode = {
						type: 'selectedFile',
						i: i,
						count: count
					};
					CKEDITOR.plugins.simpleuploads.insertSelectedFile(filePickerEditor, evData);
				}
			});
		}
		filePicker.accept = forImage ? '.jpg, .png, .jpeg, .gif, .bmp, .tiff|images/*' : '';

		filePicker.value = '';
		filePicker.simpleUploadData = {
			context: caller,
			callback: callback,
			requiresImage: forImage
		};

		// Keep focus on the editor instance.
		if (CKEDITOR.env.webkit) {
			var manager = editor.focusManager;
			if (manager && manager.lock) {
				manager.lock();
				setTimeout(function () {
					manager.unlock();
				}, 500);
			}
		}
		filePicker.click();
	}

	/**
		Returns the URL that will be used for the upload
	*/
	function getUploadUrl(editor, functionNumber, forImage) {
		var url = forImage ? editor.config.filebrowserImageUploadUrl : editor.config.filebrowserUploadUrl;
		if (url == 'base64') {
			return url;
		}

		var params = {
			CKEditor: editor.name,
			CKEditorFuncNum: functionNumber,
			langCode: editor.langCode
		};
		return addQueryString(url, params);
	}

	/**
		Returns the name that should be used for the file upload input
	*/
	function getUploadInputName(editor) {
		return editor.config.simpleuploads_inputname || 'upload';
	}

	/**
	* Adds (additional) arguments to given url.
	*
	* @param {String}
	*	url The url.
	* @param {Object}
	*	params Additional parameters.
	*/
	function addQueryString(url, params) {
		var queryString = [];

		if (!params || !url) {
			return url;
		}

		for (var key in params) {
			if ({}.hasOwnProperty.call(params, key)) {
				queryString.push(key + '=' + encodeURIComponent(params[key]));
			}
		}

		return url + (url.indexOf('?') == -1 ? '?' : '&') + queryString.join('&');
	}

	/**
		checks if a DOM event includes files checking it cross-browser
	*/
	function hasFiles(e) {
		var ev = e.data.$;
		var data = ev.dataTransfer;

		if (!data || !data.types) {
			return false;
		}
		if (data.types.contains && data.types.contains('Files') && !data.types.contains('text/html')) {
			return true;
		}
		if (data.types.indexOf && data.types.indexOf('Files') != -1) {
			return true;
		}
		return false;
	}

	function copyAttributes(img, original) {
		if (!original) {
			return;
		}
		for (var i = 0; i < original.attributes.length; i++) {
			var attrib = original.attributes[i];
			if (attrib.specified) {
				if (attrib.name != 'src' && attrib.name != 'width' && attrib.name != 'height') {
					img.setAttribute(attrib.name, attrib.value);
				}
			}
		}
		// reset size
		img.$.style.width = '';
		img.$.style.height = '';
	}

	/**
		Handles the processed response when the image/file has been uploaded
	*/
	function receivedUrl(fileUrl, data, editor, el, attribute) { // eslint-disable-line max-params
		if (el.$.nodeName.toLowerCase() == 'span') {
			// create the final img, getting rid of the fake div
			var img = new CKEDITOR.dom.element('img', editor.document);

			// Manually copy the attributes from src node
			copyAttributes(img, data.originalNode);

			// Wait to replace until the image is loaded to prevent flickering
			img.on('load', function (e) {
				e.removeListener();
				img.removeListener('error', errorListener);

				checkLoadedImage(img, editor, el, data);
			});

			img.on('error', errorListener, null, {editor: editor, element: el});

			img.data('cke-saved-src', fileUrl);
			img.setAttribute('src', fileUrl);

			// in case the user tries to get the html right now, a little protection
			el.data('cke-real-element-type', 'img');
			el.data('cke-realelement', encodeURIComponent(img.getOuterHtml()));
			el.data('cke-real-node-type', CKEDITOR.NODE_ELEMENT);

			// SVG are buggy in Firefox and IE
			// replace the image now without waiting to get confirmation
			if (/\.svg$/.test(data.name)) {
				img.removeAllListeners();
				img.replace(el);

				editor.fire('simpleuploads.finishedUpload', {name: name, element: img, data: data});

				// Correct the Undo image
				editor.fire('updateSnapshot');
			}

			return;
		}

		if (data.originalNode) {
			var newEl = data.originalNode.cloneNode(true);
			el.$.parentNode.replaceChild(newEl, el.$);
			el = new CKEDITOR.dom.element(newEl);
		} else {
			el.removeAttribute('id');
			el.removeAttribute('class');
			el.removeAttribute('contentEditable');
			el.setHtml(el.getFirst().getHtml());
		}

		el.data('cke-saved-' + attribute, fileUrl);
		el.setAttribute(attribute, fileUrl);
		editor.fire('simpleuploads.finishedUpload', {name: data.name, element: el, data: data});
	}

	var cancelledUploads = {};
	// Cancel an upload finding the element by id (eg: if the preview fails to load)
	function cancelUploadById(editor, id, reason) {
		// Allow to call it multiple times, but show the error only once.
		if (cancelledUploads[id]) {
			return;
		}

		cancelledUploads[id] = reason;

		var msg = editor.lang.simpleuploads[reason] || 'Upload cancelled: ' + reason;
		showMessage(editor, msg);

		var element = editor.document.getById(id);
		if (!element) {
			return;
		}
		var link = element.$.querySelector('.simpleuploads-uploadcancel');
		if (!link) {
			return;
		}

		link.click();
	}

	// store a reference of the native URL object because the CodeCog latex editor overwrites it
	// http://www.codecogs.com/pages/forums/pagegen.php?id=2803
	var nativeURL = window.URL || window.webkitURL;

	/**
		Escapes a string so it can be safely used as the content of a tag without security risks
	*/
	function escapeHTML(input) {
		var d = document.createElement('div');
		d.textContent = input;
		return d.innerHTML;
	}

	CKEDITOR.plugins.add('simpleuploads', {
		requires: ['filebrowser'],

		lang: 'en,ar,cs,de,es,fr,he,hu,it,ja,ko,nl,pl,pt-br,ru,tr,zh-cn', // 'en' the first one to use it as default
		icons: 'addfile,addimage', // %REMOVE_LINE_CORE%

		onLoad: function ()	{
			// In v4 this setting is global for all instances:
			CKEDITOR.addCss(getEditorCss(CKEDITOR.config));

			// CSS for container
			var node = CKEDITOR.document.getHead().append('style');
			node.setAttribute('type', 'text/css');
			var content = '.SimpleUploadsOverContainer {' + (CKEDITOR.config.simpleuploads_containerover || 'box-shadow: 0 0 10px 1px #99DD99 !important;') + '} ' +
						'.SimpleUploadsOverDialog {' + (CKEDITOR.config.simpleuploads_dialogover || 'box-shadow: 0 0 10px 4px #999999 inset !important;') + '} ' +
						'.SimpleUploadsOverCover {' + (CKEDITOR.config.simpleuploads_coverover || 'box-shadow: 0 0 10px 4px #99DD99 !important;') + '} ';

			// Inject the throbber styles in the page:
			// If this were part of the official code it should be placed in the dialog.css skin
			// We must specify the .cke_throbber for the inner divs or the reset css won't allow to use the background-color
			content += ['.cke_throbber {margin: 0 auto; width: 100px;}',
				'.cke_throbber div {float: left; width: 8px; height: 9px; margin-left: 2px; margin-right: 2px; font-size: 1px;}',
				'.cke_throbber .cke_throbber_1 {background-color: #737357;}',
				'.cke_throbber .cke_throbber_2 {background-color: #8f8f73;}',
				'.cke_throbber .cke_throbber_3 {background-color: #abab8f;}',
				'.cke_throbber .cke_throbber_4 {background-color: #c7c7ab;}',
				'.cke_throbber .cke_throbber_5 {background-color: #e3e3c7;}',
				'.simpleuploads-uploadrect {display: inline-block;height: 11px;vertical-align: middle;width: 50px;}',
				'.simpleuploads-uploadrect span {background-color: #999;display: inline-block;height: 100%;vertical-align: top;}',
				'.uploadName {display: inline-block;max-width: 180px;overflow: hidden;text-overflow: ellipsis;vertical-align: top;white-space: pre;}',
				'.uploadText {font-size:80%;}',
				'.cke_throbberMain a {cursor: pointer; font-size: 14px; font-weight:bold; padding: 4px 5px;position: absolute;right:0; text-decoration:none; top: -2px;}',
				'.cke_throbberMain {background-color: #FFF; border:1px solid #e5e5e5; padding:4px 14px 4px 4px; min-width:250px; position:absolute;}']
				.join(' ');

			if (CKEDITOR.env.ie && CKEDITOR.env.version < 11) {
				node.$.styleSheet.cssText = content;
			} else {
				node.$.innerHTML = content;
			}
		},

		init: function (editor) {
			var config = editor.config;
			// Old browsers not supported anymore
			if (typeof FormData == 'undefined') {
				return;
			}

			if (typeof config.simpleuploads_imageExtensions == 'undefined') {
				config.simpleuploads_imageExtensions = 'jpe?g|gif|png'; // eslint-disable-line camelcase
			}

			// if not defined specifically for images, reuse the default file upload url
			if (!config.filebrowserImageUploadUrl) {
				config.filebrowserImageUploadUrl = config.filebrowserUploadUrl;
			}

			if (!config.filebrowserUploadUrl && !config.filebrowserImageUploadUrl) {
				/* eslint-disable no-console */
				if (window.console && console.log) {
					console.log('The editor is missing the "config.filebrowserUploadUrl" entry to know the URL that will handle uploaded files.\r\n' +
						'It should handle the posted file as shown in Example 3: http://docs.ckeditor.com/#!/guide/dev_file_browser_api-section-example-3 \r\n' +
						'More info: http://alfonsoml.blogspot.com/2009/12/using-your-own-uploader-in-ckeditor.html');
					console[console.warn ? 'warn' : 'log']('The "SimpleUploads" plugin now is disabled.');
				}
				/* eslint-enable no-console */
				return;
			}

			// if upload URL is set to base64 data urls then exit if the browser doesn't support the file reader api
			if (config.filebrowserImageUploadUrl == 'base64' && typeof FormData == 'undefined') {
				return;
			}

			// ACF
			editor.addFeature({
				allowedContent: 'img[!src,width,height];a[!href];span[id](simpleuploads-tmpwrapper);'
			});

			// Manages the throbber animation that appears to show a lengthy operation
			CKEDITOR.dialog.prototype.showThrobber = function () {
				if (!this.throbbers) {
					this.throbbers = [];
				}

				var throbber = {
					update: function () {
						var throbberParent = this.throbberParent.$;
						var throbberBlocks = throbberParent.childNodes;
						var lastClass = throbberParent.lastChild.className;

						// From the last to the second one, copy the class from the previous one.
						for (var i = throbberBlocks.length - 1; i > 0; i--) {
							throbberBlocks[i].className = throbberBlocks[i - 1].className;
						}

						// For the first one, copy the last class (rotation).
						throbberBlocks[0].className = lastClass;
					},

					create: function (dialog) {
						var cover = dialog.throbberCover;
						if (!cover) {
							cover = CKEDITOR.dom.element.createFromHtml('<div style="background-color:rgba(255,255,255,0.95);width:100%;height:100%;top:0;left:0; position:absolute; visibility:none;z-index:100;"></div>');
							dialog.parts.close.setStyle('z-index', 101);
							cover.appendTo(dialog.parts.dialog);
							dialog.throbberCover = cover;
						}
						this.dialog = dialog;

						var mainThrobber = new CKEDITOR.dom.element('div');
						this.mainThrobber = mainThrobber;
						var throbberParent = new CKEDITOR.dom.element('div');
						this.throbberParent = throbberParent;
						var throbberTitle = new CKEDITOR.dom.element('div');
						this.throbberTitle = throbberTitle;
						cover.append(mainThrobber).addClass('cke_throbberMain');
						mainThrobber.append(throbberTitle).addClass('cke_throbberTitle');
						mainThrobber.append(throbberParent).addClass('cke_throbber');

						// Create the throbber blocks.
						var classIds = [1, 2, 3, 4, 5, 4, 3, 2];
						while (classIds.length > 0) {
							throbberParent.append(new CKEDITOR.dom.element('div')).addClass('cke_throbber_' + classIds.shift());
						}

						this.center();

						// Protection if the dialog is closed without removing the throbber
						dialog.on('hide', this.hide, this);
					},
					center: function () {
						var mainThrobber = this.mainThrobber;
						var cover = this.dialog.throbberCover;
						// Center the throbber
						var x = (cover.$.offsetWidth - mainThrobber.$.offsetWidth) / 2;
						mainThrobber.setStyle('left', x.toFixed() + 'px');

						this.centerVertical(this.dialog);
					},
					centerVertical: function (dialog) {
						// Readjust all if there are several
						var cover = dialog.throbberCover;
						var throbbers = dialog.throbbers;
						var heights = 0;
						var i;

						for (i = 0; i < throbbers.length; i++) {
							heights += throbbers[i].mainThrobber.$.offsetHeight;
						}

						var top = (cover.$.offsetHeight - heights) / 2;
						for (i = 0; i < throbbers.length; i++) {
							throbbers[i].mainThrobber.setStyle('top', top.toFixed() + 'px');
							top += throbbers[i].mainThrobber.$.offsetHeight;
						}
					},
					show: function () {
						this.create(CKEDITOR.dialog.getCurrent());

						this.dialog.throbberCover.setStyle('visibility', '');

						// Setup the animation interval.
						this.timer = setInterval(CKEDITOR.tools.bind(this.update, this), 100);
					},
					hide: function () {
						if (this.timer) {
							clearInterval(this.timer);
							this.timer = null;
						}
						var dialog = this.dialog;
						if (!dialog) {
							return;
						}

						this.dialog = null;
						this.mainThrobber.remove();
						for (var i = 0; i < dialog.throbbers.length; i++) {
							if (dialog.throbbers[i] == this) {
								dialog.throbbers.splice(i, 1);
								break;
							}
						}
						if (!dialog.throbberCover) {
							return;
						}

						if (dialog.throbbers.length > 0) {
							this.centerVertical(dialog);
							return;
						}

						dialog.throbberCover.setStyle('visibility', 'hidden');
					}
				};

				this.throbbers.push(throbber);
				throbber.show();
				return throbber;
			};

			// Add a listener to check file size and valid extensions
			editor.on('simpleuploads.startUpload', function (ev) {
				var editor = ev.editor;
				var config = editor.config;
				var file = ev.data && ev.data.file;

				if (config.simpleuploads_maxFileSize &&
					file && file.size &&
					file.size > config.simpleuploads_maxFileSize) {
					showMessage(editor, editor.lang.simpleuploads.fileTooBig);
					ev.cancel();
					return;
				}
				var name = ev.data.name;
				if (config.simpleuploads_invalidExtensions) {
					var reInvalid = new RegExp('\\.(?:' + config.simpleuploads_invalidExtensions + ')$', 'i');
					if (reInvalid.test(name)) {
						showMessage(editor, editor.lang.simpleuploads.invalidExtension);
						ev.cancel();
						return;
					}
				}
				var extensions = config.simpleuploads_acceptedExtensions;
				if (extensions) {
					if (/png/.test(extensions)) {
						// Handle automatically bmp
						// In Safari, add here support to detect .tiff as images, that we will automatically convert to png
						extensions += '|tiff|bmp';
					}

					var reAccepted = new RegExp('\\.(?:' + extensions + ')$', 'i');
					if (!reAccepted.test(name)) {
						var txt = editor.lang.simpleuploads.nonAcceptedExtension.replace('%0', config.simpleuploads_acceptedExtensions);
						showMessage(editor, txt);
						ev.cancel();
						return;
					}
				}

				// Append the CSRF field added in CKEditor 4.5.6 and required with latests versions of CKFinder
				if (CKEDITOR.tools.getCsrfToken) {
					var extraFields = ev.data.extraFields || {};
					extraFields[TOKEN_INPUT_NAME] = CKEDITOR.tools.getCsrfToken();
					ev.data.extraFields = extraFields;
				}
			});

			// Special listener that captures uploads of images and if there's some listener set for 'simpleuploads.localImageReady'
			// event, prepare an image with the local data (to check dimensions, convert between formats, resize...)
			editor.on('simpleuploads.startUpload', function (ev) {
				var data = ev.data;
				var editor = ev.editor;

				// If this function has already pre-processed the file, exit.
				if (data.image) {
					return;
				}

				// Handle here only images
				if (data.forceLink || !CKEDITOR.plugins.simpleuploads.isImageExtension(editor, data.name)) {
					return;
				}

				// If the mode hasn't been set (picked files in IE8), don't process the data
				if (!data.mode || !data.mode.type) {
					return;
				}

				// Automatically force processing on bmp
				if (/\.bmp$/.test(data.name)) {
					editor.once('simpleuploads.localImageReady', convertFromBmp);
				}

				// Safari pastes images as huge .tiff files!!!
				if (/\.tiff$/.test(data.name)) {
					editor.once('simpleuploads.localImageReady', convertFromTiff);
				}

				// As this forces an asynchronous callback use it only when there's a listener set.
				if (!editor.hasListeners('simpleuploads.localImageReady')) {
					return;
				}

				// Cancel the default processing
				ev.cancel();

				if (data.mode.type == 'base64paste') {
					// to handle multiple images in IE11, insert a marker for each one.
					// we add our class so it won't remain if it's rejected in another step
					var idTmp = CKEDITOR.plugins.simpleuploads.getTimeStampId();
					data.result = '<span id="' + idTmp + '" class="simpleuploads-tmpwrapper" style="display:none">&nbsp;</span>';
					data.mode.id = idTmp;
				}

				var img = new Image();
				img.onload = function () {
					var evData = CKEDITOR.tools.extend({}, data);
					evData.image = img;

					var result = editor.fire('simpleuploads.localImageReady', evData);

					// in v3 cancel() returns true and in v4 returns false
					// if not canceled it's the evdata object
					if (typeof result == 'boolean') {
						return;
					}

					CKEDITOR.plugins.simpleuploads.insertProcessedFile(editor, evData);
				};

				// Safari has some troubles pasting images from Finder...
				img.onerror = function () {
					img.onerror = null;
					cancelUploadById(editor, data.id, 'FailedToReadTheImage');
				};

				if (typeof data.file == 'string') {
					img.src = data.file;		// base64 encoded
				} else {
					img.src = nativeURL.createObjectURL(data.file); // FileReader
				}
			});

			if (config.simpleuploads_maximumDimensions) {
				editor.on('simpleuploads.localImageReady', checkDimension);
			}

			// workaround for image2 support
			editor.on('simpleuploads.finishedUpload', function (ev) {
				if (editor.widgets && editor.plugins.image2) {
					var element = ev.data.element;
					if (element.getName() == 'img') {
						var widget = editor.widgets.getByElement(element);
						if (widget) {
							widget.data.src = element.data('cke-saved-src');
							widget.data.width = element.$.width;
							widget.data.height = element.$.height;
						} else {
							editor.widgets.initOn(element, 'image');
						}
					}
				}
			});

			// Paste from clipboard:
			editor.on('paste', function (e) {
				var pasteData = e.data;
				var html = pasteData.html || (pasteData.type && pasteData.type == 'html' && pasteData.dataValue); // eslint-disable-line no-extra-parens

				if (!html) {
					return;
				}

				// Strip out webkit-fake-url as they are useless:
				if (CKEDITOR.env.safari && html.indexOf('webkit-fake-url') > 0) {
					showMessage(editor, editor.lang.simpleuploads.uselessSafari);
					window.open('https://bugs.webkit.org/show_bug.cgi?id=49141');
					html = html.replace(/<img src="webkit-fake-url:.*?"\s*\/?>/g, '');
				}

				// Safari really wants to annoy every developer and their users by not using a normal method to paste data
				if (CKEDITOR.env.safari && html.indexOf('"blob:') > 0) {
					html = html.replace(/<img src="(blob:.+?)"\s*\/?>/g, function (img, blobUrl) {
						if (!editor.config.filebrowserImageUploadUrl) {
							return '';
						}

						// we read from the blob url using a xhr, and that way we get the data that we need
						var imgData;
						// I would prefer not to use a synchronous request, but Apple forces me to.
						var xhr = new XMLHttpRequest();
						xhr.open('GET', blobUrl, false);
						xhr.responseType = 'blob';
						xhr.onload = function () {
							if (this.status == 200) {
								imgData = this.response; // a Blob
							}
						};
						xhr.onerror = function (e) {
							console.log('Failed to load blob Url', blobUrl, e); // eslint-disable-line no-console
						};

						xhr.send();

						if (!imgData) {
							return '';
						}

						var type = imgData.type.match(/image\/(.*)$/)[1];

						return generateUploadFromInlinePaste(editor, imgData, type);
					});
				}

				// Handles image pasting in old Firefox, and from LibreOffice
				// Replace data: images in Firefox and upload them.
				html = html.replace(/<img(?:.*?) src="(data:image\/(.{3,4});base64,.*?)"(?:.*?)>/g, function (img, imgData, type) {
					if (!editor.config.filebrowserImageUploadUrl) {
						return '';
					}

					// If it's too small then leave it as is.
					if (imgData.length < 128) {
						return img;
					}

					type = type.toLowerCase();
					if (type == 'jpeg') {
						type = 'jpg';
					}
					return generateUploadFromInlinePaste(editor, imgData, type);
				});

				if (e.data.html) {
					e.data.html = html;
				} else {
					e.data.dataValue = html;
				}
			});

			var avoidBadUndo = function (e) {
				if (editor.mode != 'wysiwyg') {
					return;
				}

				var root = editor.editable();

				// detect now if the contents include our tmp node
				if (root.$.querySelector('.simpleuploads-tmpwrapper')) {
					var move = e.name.substr(5).toLowerCase();

					// If the user tried to redo but there are no more saved images forward and this is a bad image, move back instead.
					if (move == 'redo' && editor.getCommand(move).state == CKEDITOR.TRISTATE_DISABLED) {
						move = 'undo';
					}

					// Move one extra step back/forward
					editor.execCommand(move);
				}
			};
			// on dev mode plugins might not load in the right order with empty cache
			var cmd = editor.getCommand('undo');
			if (cmd) {
				cmd.on('afterUndo', avoidBadUndo);
			}

			cmd = editor.getCommand('redo');
			if (cmd) {
				editor.getCommand('redo').on('afterRedo', avoidBadUndo);
			}

			// http://dev.ckeditor.com/ticket/10101
			editor.on('afterUndo', avoidBadUndo);
			editor.on('afterRedo', avoidBadUndo);

			// Buttons to launch the file picker easily
			// Files
			editor.addCommand('addFile', {
				exec: function (editor) {
					pickAndSendFile(editor, false, this);
				}
			});

			editor.ui.addButton('addFile', {
				label: editor.lang.simpleuploads.addFile,
				command: 'addFile',
				icon: this.path + 'icons/addfile.png', // %REMOVE_LINE_CORE%
				toolbar: 'insert',
				allowedContent: 'a[!href];span[id](simpleuploads-tmpwrapper);',
				requiredContent: 'a[href]'
			});

			// Images
			editor.addCommand('addImage', {
				exec: function (editor) {
					pickAndSendFile(editor, true, this);
				}
			});

			editor.ui.addButton('addImage', {
				label: editor.lang.simpleuploads.addImage,
				command: 'addImage',
				icon: this.path + 'icons/addimage.png', // %REMOVE_LINE_CORE%
				toolbar: 'insert',
				allowedContent: 'img[!src,width,height];span[id](simpleuploads-tmpwrapper);',
				requiredContent: 'img[src]'
			});

			var root;
			var visibleRoot;
			var pasteRoot;

			var minX = -1;
			var minY;
			var maxX;
			var maxY;
			// Hint in the main document
			var mainMinX = -1;
			var mainMinY;
			var mainMaxX;
			var mainMaxY;

			var removeBaseHighlight = function () {
				var dialog = CKEDITOR.dialog.getCurrent();
				if (dialog) {
					var div = dialog.parts.title.getParent();
					div.removeClass('SimpleUploadsOverCover');
				} else {
					editor.container.removeClass('SimpleUploadsOverContainer');
				}
			};

			editor.on('destroy', function () {
				CKEDITOR.removeListener('simpleuploads.droppedFile', removeBaseHighlight);
				CKEDITOR.document.removeListener('dragenter', CKEDITORdragenter);
				CKEDITOR.document.removeListener('dragleave', CKEDITORdragleave);
				domUnload();
			});

			function domUnload() {
				if (!root || !root.removeListener) {
					return;
				}

				pasteRoot.removeListener('paste', pasteListener);
				root.removeListener('dragenter', rootDragEnter);
				root.removeListener('dragleave', rootDragLeave);
				root.removeListener('dragover', rootDragOver);
				root.removeListener('drop', rootDropListener);

				pasteRoot = null;
				root = null;
				visibleRoot = null;
			}

			CKEDITOR.on('simpleuploads.droppedFile', removeBaseHighlight);

			function CKEDITORdragenter(e) {
				if (mainMinX == -1) {
					if (!hasFiles(e)) {
						return;
					}

					var dialog = CKEDITOR.dialog.getCurrent();
					if (dialog) {
						if (!dialog.handleFileDrop) {
							return;
						}

						var div = dialog.parts.title.getParent();
						div.addClass('SimpleUploadsOverCover');
					} else if (!editor.readOnly) {
						editor.container.addClass('SimpleUploadsOverContainer');
					}

					mainMinX = 0;
					mainMinY = 0;
					mainMaxX = CKEDITOR.document.$.body.parentNode.clientWidth;
					mainMaxY = CKEDITOR.document.$.body.parentNode.clientHeight;
				}
			}
			function CKEDITORdragleave(e) {
				if (mainMinX == -1) {
					return;
				}

				var ev = e.data.$;
				if (ev.clientX <= mainMinX || ev.clientY <= mainMinY || ev.clientX >= mainMaxX || ev.clientY >= mainMaxY) {
					removeBaseHighlight();
					mainMinX = -1;
				}
			}

			/**
				Prevent drop outside of the editor if simpleuploads_allowDropOutside is not set
			*/
			function CKEDITORdragover(e) {
				if (editor.config.simpleuploads_allowDropOutside) {
					return;
				}

				if (!hasFiles(e)) {
					return;
				}

				if (e.data.$.dataTransfer.dropEffect != 'copy') {
					e.data.$.dataTransfer.dropEffect = 'none';
					e.data.preventDefault();
					return false;
				}
			}

			CKEDITOR.document.on('dragenter', CKEDITORdragenter);
			CKEDITOR.document.on('dragleave', CKEDITORdragleave);
			CKEDITOR.document.on('dragover', CKEDITORdragover);

			function rootDropListener(e) {
				// editor
				visibleRoot.removeClass('simpleuploads-overeditor');
				minX = -1;

				// container
				// We fire an event on CKEDITOR so all the instances get notified and remove their class
				// This is an 'internal' event to the plugin
				CKEDITOR.fire('simpleuploads.droppedFile');
				mainMinX = -1;

				if (editor.readOnly) {
					e.data.preventDefault();
					return false;
				}

				var ev = e.data.$;
				var data = ev.dataTransfer;

				if (data && data.files && data.files.length > 0) {
					// Create Undo image
					editor.fire('saveSnapshot');

					// Prevent default insertion
					e.data.preventDefault();

					var dropLocation = {
						ev: ev,
						range: false,
						count: data.files.length,
						rangeParent: ev.rangeParent,
						rangeOffset: ev.rangeOffset
					};

					// store the location for IE
					if (!dropLocation.rangeParent &&
							!document.caretRangeFromPoint &&
							ev.target.nodeName.toLowerCase() != 'img') {
						var doc = editor.document.$;
						if (doc.body.createTextRange) {
							var textRange = doc.body.createTextRange();
							try {
								textRange.moveToPoint(ev.clientX, ev.clientY);

								dropLocation.range = textRange;
							} catch (err) {}  // eslint-disable-line no-empty
						}
					}

					for (var i = 0; i < data.files.length; i++) {
						var file = data.files[i];
						var id = CKEDITOR.tools.getNextId();
						var fileName = file.name;
						var evData = {
							context: ev,
							name: fileName,
							file: file,
							forceLink: ev.shiftKey, // If shift is pressed, create a link even if the drop is an image
							id: id,
							mode: {
								type: 'droppedFile',
								dropLocation: dropLocation
							}
						};

						CKEDITOR.plugins.simpleuploads.insertDroppedFile(editor, evData);
					}
				}
			}

			function rootDragEnter(e) {
				if (minX == -1) {
					if (!hasFiles(e)) {
						return;
					}

					if (!editor.readOnly) {
						visibleRoot.addClass('simpleuploads-overeditor');
					}

					var rect = visibleRoot.$.getBoundingClientRect();
					minX = rect.left;
					minY = rect.top;
					maxX = minX + visibleRoot.$.clientWidth;
					maxY = minY + visibleRoot.$.clientHeight;
				}
			}

			function rootDragLeave(e) {
				if (minX == -1) {
					return;
				}

				var ev = e.data.$;

				if (ev.clientX <= minX || ev.clientY <= minY || ev.clientX >= maxX || ev.clientY >= maxY) {
					visibleRoot.removeClass('simpleuploads-overeditor');
					minX = -1;
				}
			}

			function rootDragOver(e) {
				if (minX != -1) {
					if (editor.readOnly) {
						e.data.$.dataTransfer.dropEffect = 'none';
						e.data.preventDefault();
						return false;
					}

					// Show Copy instead of Move. Works for Chrome and Firefox
					// IE10 don't respect it
					// https://connect.microsoft.com/IE/feedback/details/1940667
					e.data.$.dataTransfer.dropEffect = 'copy';

					// IE always requires this
					// Chrome almost fixed the requirement, but it's required if the body is a single line and the user drops below it.
					if (!CKEDITOR.env.gecko) {
						e.data.preventDefault();
					}
				}
			}

			// drag & drop, paste
			editor.on('contentDom', function (/* ev */) {
				root = editor.document;
				visibleRoot = root.getBody().getParent();

				// v4 inline editing
				// ELEMENT_MODE_INLINE
				if (editor.elementMode == 3) {
					root = editor.editable();
					visibleRoot = root;
				}
				// v4 divArea
				if (editor.elementMode == 1 && 'divarea' in editor.plugins) {
					root = editor.editable();
					visibleRoot = root;
				}

				pasteRoot = editor.editable();

				// Special case for IE in forcePasteAsPlainText:
				// CKEditor uses the beforepaste event to move the target, but we can't use that to check for files,
				// so in that case, set a listener on the document on each paste
				if (CKEDITOR.env.ie && CKEDITOR.env.version >= 11 && editor.config.forcePasteAsPlainText && editor.editable().isInline()) {
					// Is an editable instance, so let's use attachListener here
					pasteRoot.attachListener(pasteRoot, 'beforepaste', function (/* bpEv */) {
						// Only once, so we can check always which editor the paste belongs to
						editor.document.on('paste', function (pEv) {
							pEv.removeListener();

							// redirect the original data to our paste listener
							pasteListener(pEv);
						}, null, {editor: editor});
					});
				} else {
					// For everyone else, use the normal paste event
					pasteRoot.on('paste', pasteListener, null, {editor: editor}, 8);
				}

				root.on('dragenter', rootDragEnter);
				root.on('dragleave', rootDragLeave);

				root.on('dragover', rootDragOver);

				root.on('drop', rootDropListener);
			});

			editor.on('contentDomUnload', domUnload);

			editor.plugins.fileDropHandler = {
				addTarget: function (target, callback) {
					target.on('dragenter', function (e) {
						if (minX == -1) {
							if (!hasFiles(e)) {
								return;
							}

							target.addClass('SimpleUploadsOverDialog');

							var rect = target.$.getBoundingClientRect();
							minX = rect.left;
							minY = rect.top;
							maxX = minX + target.$.clientWidth;
							maxY = minY + target.$.clientHeight;
						}
					});

					target.on('dragleave', function (e) {
						if (minX == -1) {
							return;
						}

						var ev = e.data.$;

						if (ev.clientX <= minX || ev.clientY <= minY || ev.clientX >= maxX || ev.clientY >= maxY) {
							target.removeClass('SimpleUploadsOverDialog');
							minX = -1;
						}
					});

					target.on('dragover', function (e) {
						if (minX != -1) {
							// Show Copy instead of Move. Works for Chrome and Firefox
							// IE10 don't respect it
							// https://connect.microsoft.com/IE/feedback/details/1940667
							e.data.$.dataTransfer.dropEffect = 'copy';

							// preventDefault with stopPropagation to avoid CKEditor 4.5 messing with the dialog
							// http://dev.ckeditor.com/ticket/13184
							e.data.preventDefault(true);
						}
					});

					target.on('drop', function (e) {
						target.removeClass('SimpleUploadsOverDialog');
						minX = -1;

						// container
						// We fire an event on CKEDITOR so all the instances get notified and remove their class
						// This is an 'internal' event to the plugin
						CKEDITOR.fire('simpleuploads.droppedFile');
						mainMinX = -1;

						var ev = e.data.$;
						var data = ev.dataTransfer;
						if (data && data.files && data.files.length > 0) {
							// Prevent default insertion
							e.data.preventDefault();

							// only one
							var maximum = 1;
							// If the element allows multiple files, use all of them
							if (callback.multiple) {
								maximum = data.files.length;
							}

							for (var i = 0; i < maximum; i++) {
								var file = data.files[i];
								var evData = {
									context: ev,
									name: file.name,
									file: file,
									id: CKEDITOR.tools.getNextId(),
									forceLink: false,
									callback: callback,
									mode: {type: 'callback'}
								};

								CKEDITOR.plugins.simpleuploads.processFileWithCallback(editor, evData);
							}
						}
					});
				}
			};
		}, // Init

		afterInit: function (editor) {
			var dataProcessor = editor.dataProcessor;
			var htmlFilter = dataProcessor && dataProcessor.htmlFilter;

			if (htmlFilter) {
				htmlFilter.addRules(htmlFilterRules, {applyToAll: true});
			}
		}
	});

	// Old browsers not supported anymore
	if (typeof FormData == 'undefined') {
		return;
	}

	// API
	CKEDITOR.plugins.simpleuploads = {
		getTimeStampId: (function () {
			var counter = 0;
			return function () {
				counter++;
				return (new Date()).toISOString().replace(/\..*/, '').replace(/\D/g, '_') + counter;
			};
		})(),

		isImageExtension: function (editor, filename) {
			var extensions = editor.config.simpleuploads_imageExtensions;
			if (!extensions) {
				return false;
			}

			if (/png/.test(extensions)) {
				// In some browser it used to paste as .bmp, not sure anymore
				// For Safari, add here support to detect .tiff as images, that we will automatically convert to png
				extensions += '|bmp|tiff';
			}
			var imageRegexp = new RegExp('\\.(?:' + extensions + ')$', 'i');
			return imageRegexp.test(filename);
		},

		// Main entry point for callbacks
		insertProcessedFile: function (editor, evData) {
			evData.element = null;
			evData.id = this.getTimeStampId(); // new id
			var that = this;

			switch (evData.mode.type) {
				case 'selectedFile':
					window.setTimeout(function () {
						that.insertSelectedFile(editor, evData);
					}, 50);
					break;

				case 'pastedFile':
					this.insertPastedFile(editor, evData);
					break;

				case 'callback':
					window.setTimeout(function () {
						that.processFileWithCallback(editor, evData);
					}, 50);
					break;

				case 'droppedFile':
					this.insertDroppedFile(editor, evData);
					break;

				case 'base64paste':
					this.insertBase64File(editor, evData);
					break;

				default:
					showMessage(editor, 'Error, no valid type in callback ' + evData.mode);
					break;
			}
		},

		// Insert a file from the toolbar buttons
		insertSelectedFile: function (editor, evData) {
			var mode = evData.mode;
			var i = mode.i;
			var count = mode.count;

			// Upload the file
			if (!uploadFile(editor, evData)) {
				return;
			}

			var element = evData.element;
			if (!element) {
				return;
			}

			if (count == 1) {
				var selection = editor.getSelection();
				var selected = selection.getSelectedElement();
				var originalNode;

				// If it's just one image and the user has another one selected, replace it
				if (selected && selected.getName() == 'img' && element.getName() == 'span') {
					originalNode = selected.$;
				}

				// Image2 widget
				if (editor.widgets) {
					var focused = editor.widgets.focused;
					if (focused && focused.wrapper.equals(selected)) {
						originalNode = selected.$.querySelector('img');
					}
				}

				// a link
				if (element.getName() == 'a') {
					var parent = selected;
					var ranges = selection.getRanges();
					var range = ranges && ranges[0];

					if (!parent && ranges && ranges.length == 1) {
						parent = range.startContainer.$;
						if (parent.nodeType == document.TEXT_NODE) {
							parent = parent.parentNode;
						}
					}

					while (parent && parent.nodeType == document.ELEMENT_NODE && parent.nodeName.toLowerCase() != 'a') {
						parent = parent.parentNode;
					}

					if (parent && parent.nodeName && parent.nodeName.toLowerCase() == 'a') {
						originalNode = parent;
					}
					// there was no link, check the best way to create one:

					// create a link
					if (!originalNode && range && (selected || !range.collapsed)) {
						var style = new CKEDITOR.style({element: 'a', attributes: {href: '#'}});
						style.type = CKEDITOR.STYLE_INLINE; // need to override... dunno why.
						style.applyToRange(range);

						parent = range.startContainer.$;
						if (parent.nodeType == document.TEXT_NODE) {
							parent = parent.parentNode;
						}

						originalNode = parent;
					}
				}

				if (originalNode) {
					originalNode.parentNode.replaceChild(element.$, originalNode);
					evData.originalNode = originalNode;
					editor.fire('saveSnapshot');
					// Just in case...
					processFinishedUpload(evData);
					return;
				}
			}

			// insert a space between links
			if (i > 0 && element.getName() == 'a') {
				editor.insertHtml('&nbsp;');
			}

			editor.insertElement(element);
			setupCancelButton(editor, evData);
			// Just in case...
			processFinishedUpload(evData);
		},

		// Insert a file that has been pasted into the content (as File)
		insertPastedFile: function (editor, evData) {
			checkSafariBugPastedFiles(editor, evData);

			// Upload the file
			if (!uploadFile(editor, evData)) {
				return;
			}

			var element = evData.element;

			var dialog = evData.mode.dialog;
			if (dialog) {
				editor.fire('updateSnapshot');
				editor.insertElement(element);
				editor.fire('updateSnapshot');
				// Just in case...
				processFinishedUpload(evData);
			} else {
				// Insert in the correct position after the pastebin has been removed
				var processElement = function () {
					// Check if there's a valid selection or if it's the pastebin
					var ranges = editor.getSelection().getRanges();

					if (ranges.length == 0) {
						// Put back in the queue
						window.setTimeout(processElement, 0);
						return;
					}
					// verify that it has really been removed
					if (editor.editable().$.querySelector('#cke_pastebin')) {
						// Put back in the queue
						window.setTimeout(processElement, 0);
						return;
					}

					if (cancelledUploads[evData.id]) {
						if (evData.xhr) {
							evData.xhr.abort();
						}
						return;
					}

					editor.fire('updateSnapshot');
					editor.insertElement(element);
					editor.fire('updateSnapshot');
					setupCancelButton(editor, evData);

					// Just in case...
					processFinishedUpload(evData);
				};
				window.setTimeout(processElement, 0);
			}
		},

		// The evData includes a callback that takes care of everything (a file dropped in a dialog)
		processFileWithCallback: function (editor, evData) {
			uploadFile(editor, evData);
		},

		insertSingleDroppedFile: function (element, target, range, evData) {
			var elementName = element.getName();

			if (target.nodeName.toLowerCase() == 'img' && elementName == 'span') {
				target.parentNode.replaceChild(element.$, target);
				evData.originalNode = target;
				return true;
			}

			if (elementName == 'a') {
				var start;
				if (range.startContainer) {
					start = range.startContainer;
					if (start.nodeType == document.TEXT_NODE) {
						start = start.parentNode;
					} else if (range.startOffset < start.childNodes.length) {
						start = start.childNodes[range.startOffset];
					}
				} else {
					start = range.parentElement();
				}

				if (!start || target.nodeName.toLowerCase() == 'img') {
					start = target;
				}

				var parent = start;
				while (parent && parent.nodeType == document.ELEMENT_NODE && parent.nodeName.toLowerCase() != 'a') {
					parent = parent.parentNode;
				}

				if (parent && parent.nodeName && parent.nodeName.toLowerCase() == 'a') {
					parent.parentNode.replaceChild(element.$, parent);
					evData.originalNode = parent;
					return true;
				}
				// dropping on an image without a parent link
				if (start.nodeName.toLowerCase() == 'img') {
					parent = start.ownerDocument.createElement('a');
					parent.href = '#';
					start.parentNode.replaceChild(parent, start);
					parent.appendChild(start);

					parent.parentNode.replaceChild(element.$, parent);
					evData.originalNode = parent;
					return true;
				}
			}
			return false;
		},

		insertDroppedFile: function (editor, evData) {
			if (!uploadFile(editor, evData)) {
				return;
			}

			var element = evData.element;
			var dropLocation = evData.mode.dropLocation;
			var range = dropLocation.range;
			var ev = dropLocation.ev;
			var count = dropLocation.count;

			// if we're adding several links, add a space between them
			if (range && element.getName() == 'a') {
				if (range.pasteHTML) {
					range.pasteHTML('&nbsp;'); // simple space doesn't work
				} else {
					range.insertNode(editor.document.$.createTextNode(' '));
				}
			}

			var target = ev.target;
			if (!range) {
				var doc = editor.document.$;
				// Move to insertion point
				/*
				standard way: only implemented in Firefox 20
				if (document.caretPositionFromPoint)
				{
					var caret = document.caretPositionFromPoint(ev.pageX, ev.pageY),
						textNode = caret.offsetNode,
						offset = caret.offset;
				}
				*/

				if (dropLocation.rangeParent) {
					// Firefox, custom properties in event.
					// it seems that they aren't preserved in the ev after resending back the info
					var node = dropLocation.rangeParent;
					var offset = dropLocation.rangeOffset;
					range = doc.createRange();
					range.setStart(node, offset);
					range.collapse(true);
				} else if (document.caretRangeFromPoint) {
					// Webkit, old documentView API
					range = doc.caretRangeFromPoint(ev.clientX, ev.clientY);
				} else if (target.nodeName.toLowerCase() == 'img') {
					// IE
					range = doc.createRange();
					range.selectNode(target);
				} else if (document.body.createTextRange) {
					// IE
					var textRange = doc.body.createTextRange();
					try {
						textRange.moveToPoint(ev.clientX, ev.clientY);

						range = textRange;
					} catch (err) {
						range = doc.createRange();
						range.setStartAfter(doc.body.lastChild);
						range.collapse(true);
					}
				}
				dropLocation.range = range;
			}

			var handled = false;

			if (count == 1) {
				handled = this.insertSingleDroppedFile(element, target, range, evData);
			}

			if (!handled) {
				if (range) {
					if (range.pasteHTML) {
						range.pasteHTML(element.$.outerHTML);
					} else {
						range.insertNode(element.$);
					}
				} else {
					editor.insertElement(element);
				}
			}

			setupCancelButton(editor, evData);
			editor.fire('saveSnapshot');
			// Just in case...
			processFinishedUpload(evData);
		},

		insertBase64File: function (editor, evData) {
			delete evData.result;

			var id = evData.mode.id;
			var tmp = editor.document.getById(id);

			if (!uploadFile(editor, evData)) {
				tmp.remove();
				if (evData.result) {
					editor.insertHTML(evData.result);
				}

				return;
			}

			/* Safari fails here
			editor.getSelection().selectElement(tmp);
			editor.insertElement(evData.element);
			*/
			evData.element.replace(tmp);

			setupCancelButton(editor, evData);
		}
	};

	// Creates the element, but doesn't insert it
	function createPreview(editor, data) {
		var isImage = CKEDITOR.plugins.simpleuploads.isImageExtension(editor, data.name);
		var showImageProgress = !editor.config.simpleuploads_hideImageProgress;
		var element;

		// Create and insert our element
		if (!data.forceLink && isImage && showImageProgress) {
			element = createSVGAnimation(data.file, data.id, editor);
		} else {
			if (isImage && !data.forceLink) {
				element = new CKEDITOR.dom.element('span', editor.document);
			} else {
				element = new CKEDITOR.dom.element('a', editor.document);
			}

			element.setAttribute('id', data.id);
			element.setAttribute('class', 'simpleuploads-tmpwrapper');

			var html = '<span class="uploadName">' + escapeHTML(data.name) + '</span>' +
				' <span class="simpleuploads-uploadrect"><span id="rect' + data.id + '"></span></span>' +
				' <span id="text' + data.id + '" class="uploadText"> </span><span class="simpleuploads-uploadcancel">x</span>';
			element.setHtml(html);
		}
		// Prevent selection handles in IE
		element.setAttribute('contentEditable', false);

		data.element = element;
	}

	function errorListener(e) {
		var data = e.listenerData;
		var editor = data.editor;
		var element = data.element;
		e.removeListener();
		// This means that the server has returned a URL that it's wrong
		showMessage(editor, editor.lang.simpleuploads.badUrl + ': "' + e.sender.data('cke-saved-src') + '"');
		element.remove();
	}

	function checkLoadedImage(img, editor, el, data) {
		if (img.$.naturalWidth === 0) {
			// When replacing an image, IE might fire the load event, but it still uses the old data
			// Firefox might still keep the old size
			window.setTimeout(function () {
				checkLoadedImage(img, editor, el, data);
			}, 50);
			return;
		}

		img.replace(el);
		img.setAttribute('width', img.$.naturalWidth);
		img.setAttribute('height', img.$.naturalHeight);

		editor.fire('simpleuploads.finishedUpload', {name: data.name, element: img, data: data});

		// Correct the Undo image
		editor.fire('updateSnapshot');
	}

	// Safari might fail to allow to paste files, and it seems that the only way to check is by trying to read it
	function checkSafariBugPastedFiles(editor, data) {
		if (!CKEDITOR.env.safari) {
			return;
		}

		var reader = new FileReader();
		reader.onload = function () {
			// nothing, it's OK
			reader.onload = null;
			reader.onerror = null;
			reader = null;
		};
		reader.onerror = function () {
			reader.onload = null;
			reader.onerror = null;
			reader = null;
			cancelUploadById(editor, data.id, 'FailedToReadTheFile');
		};

		reader.readAsDataURL(data.file);
	}

	// Tries to get the response data correctly from the xhr
	function parseServerResponse(xhr, data) {
		var fileUrl;
		var msg;

		// try to check if the response is in JSON format http://docs.ckeditor.com/#!/guide/dev_file_upload
		try {
			var o = JSON.parse(xhr.responseText);
			if (o && o.url) {
				fileUrl = o.url;
			}
			if (o && o.error && o.error.message) {
				msg = o.error.message;
			}
		} catch (err) { } // eslint-disable-line no-empty

		if (!fileUrl && !msg) {
			// old javascript response
			// Upon finish, get the url and update the file
			// var parts = xhr.responseText.match(/2,\s*("|')(.*?[^\\]?)\1(?:,\s*\1(.*?[^\\]?)\1)?\s*\)/),
			// var parts = xhr.responseText.match(/\((?:"|')?\d+(?:"|')?,\s*("|')(.*?[^\\]?)\1(?:,\s*(.*?))?\s*\)\s*;?\s*<\/script>/),
			var parts = xhr.responseText.match(/\((?:"|')?\d+(?:"|')?,\s*("|')(.*?[^\\]?)\1(?:,\s*(.*?))?\s*\)\s*;?/);

			fileUrl = parts && parts[2];
			msg = parts && parts[3];

			// The server response usually is automatically parsed by the js engine, but in this case we get the 'raw content'
			// and must take care of un-escaping it.
			// So far I haven't been able to find a single function that does it correctly in all the cases
			if (fileUrl) {
				fileUrl = fileUrl.replace(/\\'/g, '\'');

				// Try to handle URLs with escaped chars like 51-Body/\u00E6\u00F8\u00E5.jpg
				try {
					var tmp = JSON.parse('{"url":"' + fileUrl + '"}');
					if (tmp && tmp.url) {
						fileUrl = tmp.url;
					}
				} catch (err) { } // eslint-disable-line no-empty
			}

			if (msg) {
				// find out if it was a function or a string message:
				var matchFunction = msg.match(/function\(\)\s*\{(.*)\}/);
				if (matchFunction) {
					msg = new Function(matchFunction[1]); // eslint-disable-line no-new-func
				} else {
					var first = msg.substring(0, 1);
					if (first == '\'' || first == '"') {
						msg = msg.substring(1, msg.length - 1);
					}
				}
			}

			if (!parts) {
				msg = 'Error posting the file to ' + data.url + '\r\nInvalid data returned (check console)';
				if (window.console) {
					console.log(xhr.responseText, xhr); // eslint-disable-line no-console
				}
			}
		}

		return {
			fileUrl: fileUrl,
			msg: msg
		};
	}

	// Non 200 status code means that there's an error at the server and the user probably can't do anything to fix it
	// If there's something wrong with the upload it should be checked before the upload starts
	function showErrorMessageUpload(xhr, data, editor) {
		if (xhr.status == 413) {
			showMessage(editor, editor.lang.simpleuploads.fileTooBig);
		} else {
			// Checks if there is a message specific to this status, then defaults to generic error
			var errorMessage = editor.lang.simpleuploads['httpStatus' + xhr.status];
			if (!errorMessage) {
				errorMessage = editor.lang.simpleuploads.errorPostFile;
				errorMessage += ' ' + xhr.status;
			}

			showMessage(editor, errorMessage.replace('%0', data.url));
		}
		if (window.console) {
			console.log(xhr); // eslint-disable-line no-console
		}
	}

	// Sets up a XHR object to handle the upload
	function createXHRupload(editor, data) {
		var isImage = CKEDITOR.plugins.simpleuploads.isImageExtension(editor, data.name);
		var attribute = 'href';
		var forImage = false;

		if (!data.forceLink && isImage) {
			attribute = 'src';
			forImage = true;
		}

		if (data.callback) {
			data.callback.setup(data);
		}

		if (!data.url) {
			data.url = getUploadUrl(editor, 2, forImage);
		}

		if (data.requiresImage && !isImage) {
			showMessage(editor, editor.lang.simpleuploads.nonImageExtension);
			return null;
		}

		// if it already has failed to load the image/file get out
		if (cancelledUploads[data.id]) {
			return null;
		}

		var result = editor.fire('simpleuploads.startUpload', data);
		// in v3 cancel() returns true and in v4 returns false
		// if not canceled it's the data object, so let's use that.
		if (typeof result == 'boolean') {
			return null;
		}

		if (!data.url) {
			return null;
		}

		// instead of uploading, use base64 encoded data
		if (data.url == 'base64') {
			if (typeof data.file == 'string') {
				setTimeout(function () {
					finishedLoadingBase64(data, editor, attribute, data.file);
				}, 100);
				return {};
			}

			var reader = new FileReader();
			reader.onload = function () {
				setTimeout(function () {
					finishedLoadingBase64(data, editor, attribute, reader.result);
				}, 100);
			};

			reader.readAsDataURL(data.file);
			return {};
		}

		var xhr = data.xhr || new XMLHttpRequest();
		var target = xhr.upload;

		// nice progress effect. Opera used to lack xhr.upload
		if (target) {
			target.onprogress = function (evt) {
				updateProgress(editor, data.id, evt);
			};
		}

		data.xhr = xhr;

		// Upload the file
		xhr.open('POST', data.url);
		xhr.onload = function () {
			var id = data.id;
			var el = editor.document.getById(id);
			var fileUrl;
			var msg;

			// final update
			updateProgress(editor, id, null);
			// Correct the Undo image
			editor.fire('updateSnapshot');

			var evtData = {xhr: xhr, data: data, element: el};
			var result = editor.fire('simpleuploads.serverResponse', evtData);

			// in v3 cancel() returns true and in v4 returns false
			// if not canceled it's the evdata object
			if (typeof result == 'boolean') {
				return; // if the listener has Cancelled the event, exit and we suppose that it took care of everything by itself.
			}

			// Check if the event has been listened and performed its own parsing
			if (typeof evtData.url == 'undefined') {
				if (xhr.status == 200) {
					var parsed = parseServerResponse(xhr, data);
					if (parsed) {
						fileUrl = parsed.fileUrl;
						msg = parsed.msg;
					}
				} else {
					showErrorMessageUpload(xhr, data, editor);
				}
			} else {
				fileUrl = evtData.url;
				msg = '';
			}

			editor.fire('simpleuploads.endUpload', {
				name: data.name,
				ok: Boolean(fileUrl),
				xhr: xhr,
				data: data
			});

			if (!fileUrl && msg) {
				showMessage(editor, msg);
			}

			if (data.callback) {
				data.callback.upload(fileUrl, msg, data);
				return;
			}

			// As the placeholder is inserted asynchrously (eg: during paste) in very strange situations it might happen that the upload finishes
			// before the target element is in the DOM.
			data.finishedUpload = {
				fileUrl: fileUrl,
				editor: editor,
				attribute: attribute
			};

			processFinishedUpload(data);
		};

		xhr.onerror = function (e) {
			showMessage(editor, editor.lang.simpleuploads.xhrError.replace('%0', data.url));
			if (window.console) {
				console.log(e); // eslint-disable-line no-console
			}

			cleanupFailedUpload(editor, data);
		};
		xhr.onabort = function () {
			if (data.callback) {
				data.callback.upload(null, null, data);
				return;
			}
			cleanupFailedUpload(editor, data);
		};

		// CORS https://developer.mozilla.org/en-US/docs/HTTP/Access_control_CORS
		xhr.withCredentials = true;

		return xhr;
	}

	function finishedLoadingBase64(data, editor, attribute, fileUrl) {
		if (data.callback) {
			data.callback.upload(fileUrl, '', data);
			return;
		}

		// As the placeholder is inserted asynchrously (eg: during paste) the upload finishes
		// before the target element is in the DOM.
		data.finishedUpload = {
			fileUrl: fileUrl,
			editor: editor,
			attribute: attribute
		};

		processFinishedUpload(data);
	}

	// Clean up the DOM if the upload fails or is aborted
	function cleanupFailedUpload(editor, data) {
		var el = editor.document.getById(data.id);
		if (el) {
			if (data.originalNode) {
				el.$.parentNode.replaceChild(data.originalNode, el.$);
			} else {
				el.remove();
			}
		}
		// Correct undo image
		editor.fire('updateSnapshot');
	}

	// As the placeholder is inserted asynchrously (eg: during paste) in very strange situations it might happen that the upload finishes
	// before the target element is in the DOM.
	function processFinishedUpload(data) {
		var finishedUpload = data.finishedUpload;
		if (!finishedUpload) {
			return;
		}

		var	fileUrl = finishedUpload.fileUrl;
		var editor = finishedUpload.editor;
		var attribute = finishedUpload.attribute;
		var id = data.id;
		var el = editor.document.getById(id);

		// If the element doesn't exist it means that the user has deleted it,
		// or pressed undo while uploading.
		// It can also happen if the upload finishes before the element is inserted.
		// So let's get out.
		if (!el) {
			return;
		}

		if (fileUrl) {
			receivedUrl(fileUrl, data, editor, el, attribute);
		} else if (data.originalNode) {
			el.$.parentNode.replaceChild(data.originalNode, el.$);
		} else {
			el.remove();
		}

		// Correct undo image
		editor.fire('updateSnapshot');
	}

	// Takes care of uploading the file using XHR
	function uploadFile(editor, data) {
		if (!data.callback) {
			createPreview(editor, data);
		}

		var xhr = createXHRupload(editor, data);
		if (!xhr) {
			data.result = data.result || '';
			return false;
		}
		// FileReader
		if (!xhr.send) {
			return true;
		}

		if (data.callback && data.callback.start) {
			data.callback.start(data);
		}

		var inputName = data.inputName || getUploadInputName(editor);

		if (typeof data.file == 'string') {
			sendBase64File(data, xhr, inputName);
		} else {
			sendBlobFile(data, xhr, inputName);
		}

		return true;
	}

	function sendBlobFile(data, xhr, inputName) {
		var formdata = new FormData();
		formdata.append(inputName, data.file, data.name);
		// Add extra fields if provided
		if (data.extraFields) {
			var obj = data.extraFields;
			for (var prop in obj) {
				if ({}.hasOwnProperty.call(obj, prop)) {
					formdata.append(prop, obj[prop]);
				}
			}
		}
		if (data.extraHeaders) {
			var headers = data.extraHeaders;
			for (var header in headers) {
				if ({}.hasOwnProperty.call(headers, header)) {
					xhr.setRequestHeader(header, headers[header]);
				}
			}
		}
		xhr.send(formdata);
	}

	function sendBase64File(data, xhr, inputName) {
		// Create the multipart data upload.
		var BOUNDARY = '---------------------------1966284435497298061834782736';
		var rn = '\r\n';
		var req = '--' + BOUNDARY;
		var type = data.name.match(/\.(\w+)$/)[1];

		req += rn + 'Content-Disposition: form-data; name="' + inputName + '"; filename="' + data.name + '"';
		req	+= rn + 'Content-type: image/' + type;
		req += rn + rn + window.atob(data.file.split(',')[1]);
		req += rn + '--' + BOUNDARY;

		// Add extra fields if provided
		if (data.extraFields) {
			var obj = data.extraFields;
			for (var prop in obj) {
				if ({}.hasOwnProperty.call(obj, prop)) {
					req += rn + 'Content-Disposition: form-data; name="' + unescape(encodeURIComponent(prop)).replace(/=/g, '\\=') + '"'; // eslint-disable-line no-div-regex
					req += rn + rn + unescape(encodeURIComponent(obj[prop]));
					req += rn + '--' + BOUNDARY;
				}
			}
		}

		req += '--';

		xhr.setRequestHeader('Content-Type', 'multipart/form-data; boundary=' + BOUNDARY);

		var bufferData = new ArrayBuffer(req.length);
		var ui8a = new Uint8Array(bufferData, 0);
		for (var i = 0; i < req.length; i++) {
			ui8a[i] = req.charCodeAt(i) & 0xff;
		}
		xhr.send(ui8a);
	}

	function updateProgress(editor, id, evt) {
		if (!editor.document || !editor.document.$) {
			return;
		}

		var dialog = CKEDITOR.dialog.getCurrent();
		var doc = (dialog ? CKEDITOR : editor).document.$;
		var rect = doc.getElementById('rect' + id);
		var text = doc.getElementById('text' + id);
		var value;
		var textValue;

		if (evt) {
			if (!evt.lengthComputable) {
				return;
			}

			value = (100 * evt.loaded / evt.total).toFixed(2) + '%';
			textValue = (100 * evt.loaded / evt.total).toFixed() + '%';
		} else {
			textValue = editor.lang.simpleuploads.processing;
			value = '100%';
		/*
			if (text)
			{
				text.parentNode.removeChild(text);
				text = null;
			}
		*/
		}
		if (rect) {
			rect.setAttribute('width', value);
			rect.style.width = value;
			if (!evt) {
				var parent = rect.parentNode;
				if (parent && parent.className == 'simpleuploads-uploadrect') {
					parent.parentNode.removeChild(parent);
				}
			}
		}
		if (text) {
			text.firstChild.nodeValue = textValue;
			if (!evt) {
				// Remove cancel button
				var sibling = text.nextSibling;
				if (sibling && sibling.nodeName.toLowerCase() == 'a') {
					sibling.parentNode.removeChild(sibling);
				}
			}
		}
	}

	// Show a grayscale version of the image that animates toward the full color version
	function createSVGAnimation(file, id, editor) {
		var element = new CKEDITOR.dom.element('span', editor.document);
		var div = element.$;
		var useURL;
		var doc = editor.document.$;
		var span = doc.createElement('span');

		element.setAttribute('id', id);
		element.setAttribute('class', 'simpleuploads-tmpwrapper');
		var rectSpan = doc.createElement('span');
		rectSpan.setAttribute('id', 'text' + id);
		rectSpan.appendChild(doc.createTextNode('0 %'));
		div.appendChild(span);
		span.appendChild(rectSpan);

		var cancelSpan = doc.createElement('span');
		cancelSpan.appendChild(doc.createTextNode('x'));
		span.appendChild(cancelSpan);

		if (typeof file != 'string') {
			if (!nativeURL || !nativeURL.revokeObjectURL) {
				return element;
			}

			useURL = true;
		}

		var svg = doc.createElementNS('http://www.w3.org/2000/svg', 'svg');
		svg.setAttribute('id', 'svg' + id);

		// just to find out the image dimensions as they are needed for the svg block
		var img = doc.createElement('img');
		if (useURL) {
			img.onload = function () {
				if (this.onload) {
					nativeURL.revokeObjectURL(this.src);
					this.onload = null;
				}
				this.onerror = null;

				// in IE it's inserted with the HTML, so we can't reuse the svg object
				var svg = doc.getElementById('svg' + id);
				if (svg) {
					svg.setAttribute('width', this.width + 'px');
					svg.setAttribute('height', this.height + 'px');
				}
				// Chrome
				var preview = doc.getElementById(id);
				if (preview) {
					preview.style.width = this.width + 'px';
				}
			};
			img.onerror = function () {
				cancelUploadById(editor, id, 'FailedToComputePreviewImageSize');
			};
			img.src = nativeURL.createObjectURL(file);
		} else {
			// base64 data, dimensions are available right now in Firefox
			img.src = file;
			// extra protection
			img.onload = function () {
				this.onload = null;

				// we're pasting so it's inserted with the HTML, so we can't reuse the svg object
				var svg = doc.getElementById('svg' + id);
				if (svg) {
					svg.setAttribute('width', this.width + 'px');
					svg.setAttribute('height', this.height + 'px');
				}
			};
			svg.setAttribute('width', img.width + 'px');
			svg.setAttribute('height', img.height + 'px');
		}

		div.appendChild(svg);

		var filter = doc.createElementNS('http://www.w3.org/2000/svg', 'filter');
		filter.setAttribute('id', 'SVGdesaturate');
		svg.appendChild(filter);

		var feColorMatrix = doc.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
		feColorMatrix.setAttribute('type', 'saturate');
		feColorMatrix.setAttribute('values', '0');
		filter.appendChild(feColorMatrix);

		var clipPath = doc.createElementNS('http://www.w3.org/2000/svg', 'clipPath');
		clipPath.setAttribute('id', 'SVGprogress' + id);
		svg.appendChild(clipPath);

		var rect = doc.createElementNS('http://www.w3.org/2000/svg', 'rect');
		rect.setAttribute('id', 'rect' + id);
		rect.setAttribute('width', '0');
		rect.setAttribute('height', '100%');
		clipPath.appendChild(rect);

		var image = doc.createElementNS('http://www.w3.org/2000/svg', 'image');
		image.setAttribute('width', '100%');
		image.setAttribute('height', '100%');

		function loaded() {
			nativeURL.revokeObjectURL(image.getAttributeNS('http://www.w3.org/1999/xlink', 'href'));
			image.removeEventListener('load', loaded, false);
			image.removeEventListener('error', failed, false);
		}
		function failed() {
			image.removeEventListener('load', loaded, false);
			image.removeEventListener('error', failed, false);
			cancelUploadById(editor, id, 'FailedToLoadPreviewImage');
		}

		if (useURL) {
			image.setAttributeNS('http://www.w3.org/1999/xlink', 'href', nativeURL.createObjectURL(file));
			image.addEventListener('load', loaded, false);
			image.addEventListener('error', failed, false);
		} else {
			image.setAttributeNS('http://www.w3.org/1999/xlink', 'href', file);
		}

		var image2 = image.cloneNode(true);
		image.setAttribute('filter', 'url(#SVGdesaturate)');
		image.style.opacity = '0.5';

		svg.appendChild(image);

		image2.setAttribute('clip-path', 'url(#SVGprogress' + id + ')');
		svg.appendChild(image2);

		return element;
	}

	function createSimpleUpload(editor, dialogName, definition, element) {
		if (element.type == 'file') {
			return;
		}

		var filebrowser = element.filebrowser;
		var forImage = dialogName.substr(0, 5) == 'image' || filebrowser.requiresImage;
		var targetField = filebrowser.target && filebrowser.target.split(':');

		var callback = {
			targetField: targetField,
			multiple: filebrowser.multiple,
			setup: function (data) {
				if (!definition.uploadUrl) {
					return;
				}

				if (forImage) {
					data.requiresImage = true;
				}

				if (definition.uploadUrl == 'base64') {
					data.url = definition.uploadUrl;
				} else {
					var params = {
						CKEditor: editor.name,
						CKEditorFuncNum: 2,
						langCode: editor.langCode
					};

					data.url = addQueryString(definition.uploadUrl, params);
				}
			},
			start: function (data) {
				var dialog = CKEDITOR.dialog.getCurrent();
				var throbber = data.throbber = dialog.showThrobber();

				if (data.xhr) {
					var html = '<span class="uploadName">' + escapeHTML(data.name) + '</span>' +
						' <span class="simpleuploads-uploadrect"><span id="rect' + data.id + '"></span></span>' +
						' <span id="text' + data.id + '" class="uploadText"> </span><a>x</a>';

					throbber.throbberTitle.setHtml(html);

					var xhr = data.xhr;
					if (throbber.timer) {
						clearInterval(throbber.timer);
						throbber.timer = null;
					}
					throbber.throbberParent.setStyle('display', 'none');
					throbber.throbberTitle.getLast().on('click', function () {
						xhr.abort();
					});

					// protection to check that the upload isn't pending when forcing to close the dialog
					dialog.on('hide', function () {
						if (xhr.readyState == 1) {
							xhr.abort();
						}
					});
				}

				throbber.center();
			},
			upload: function (url, msg, data) {
				var dialog = CKEDITOR.dialog.getCurrent();
				if (data.throbber) {
					data.throbber.hide();
				}

				if (typeof msg == 'function' && msg.call(data.context.sender) === false) {
					return;
				}

				if (filebrowser.onSelect && filebrowser.onSelect(url, msg, data) === false) {
					return;
				}

				if (!url) {
					return;
				}

				dialog.getContentElement(targetField[0], targetField[1]).setValue(url);
				dialog.selectPage(targetField[0]);
			}
		};

		if (filebrowser.action == 'QuickUpload') {
			definition.hasQuickUpload = true;
			definition.onFileSelect = null;
			if (!editor.config.simpleuploads_respectDialogUploads) {
				element.label = forImage ? editor.lang.simpleuploads.addImage : editor.lang.simpleuploads.addFile;

				element.onClick = function (evt) {
					// 'element' here means the definition object, so we need to find the correct
					// button to scope the event call
					pickAndSendFile(editor, forImage, evt, callback);
					return false;
				};

				var picker = definition.getContents(element['for'][0]).get(element['for'][1]); // eslint-disable-line dot-notation
				picker.hidden = true;
			}
		} else {
			// if the dialog has already been configured with quickUpload there's no need to use the file browser config
			if (definition.hasQuickUpload) {
				return;
			}

			if (filebrowser.onSelect) {
				definition.onFileSelect = filebrowser.onSelect;
			}
		}

		if (!editor.plugins.fileDropHandler) {
			return;
		}

		if (filebrowser.action == 'QuickUpload') {
			definition.uploadUrl = filebrowser.url;
		}

		var original = definition.onShow || function () {};
		definition.onShow = CKEDITOR.tools.override(original, function (original) {
			return function (e) {
				// Revert to the original after first run
				definition.onShow = original;

				if (typeof original == 'function') {
					original.call(this, e);
				}

				if (filebrowser.action != 'QuickUpload' && definition.hasQuickUpload) {
					return;
				}

				var dialog = this;
				if (dialog.handleFileDrop) {
					return;
				}

				dialog.handleFileDrop = true;
				dialog.getParentEditor().plugins.fileDropHandler.addTarget(dialog.parts.contents, callback);
			};
		});
	}

	// Searches for elements in the dialog definition where we can apply our enhancements
	function applySimpleUpload(editor, dialogName, definition, elements) {
		for (var key in elements) {
			if ({}.hasOwnProperty.call(elements, key)) {
				var element = elements[key];
				// If due to some customization or external library the object isn't valid, skip it.
				if (!element) {
					continue;
				}

				if (element.type == 'hbox' || element.type == 'vbox' || element.type == 'fieldset') {
					applySimpleUpload(editor, dialogName, definition, element.children);
				}

				if (element.filebrowser && element.filebrowser.url) {
					createSimpleUpload(editor, dialogName, definition, element);
				}
			}
		}
	}

	function setupCancelButton(editor, data) {
		var element = editor.document.getById(data.id);
		if (!element) {
			return;
		}

		var links = element.$.getElementsByTagName('a');
		if (!links || links.length == 0) {
			links = element.$.getElementsByTagName('span');
			if (!links || links.length == 0) {
				return;
			}
		}

		for (var i = 0; i < links.length; i++) {
			var link = links[i];
			if (link.innerHTML == 'x') {
				link.className = 'simpleuploads-uploadcancel';
				link.onclick = function () {
					if (data.xhr) {
						data.xhr.abort();
					}
				};
			}
		}
	}

	function pasteListener(e) {
		var editor = e.listenerData.editor;
		var dialog = e.listenerData.dialog;
		var i;
		var item;

		// We want IE11 here to embed images as base64 (at least for the moment)
		// later use them as blob if we aren't in a dialog

		// In IE11 we use the images at this point only if forcePasteAsPlainText has been set
		// It doesn't work due to https://connect.microsoft.com/IE/feedback/details/813618/calling-xhr-open-in-a-paste-event-throws-an-access-denied-error
		var data = (e.data && e.data.$.clipboardData) || (editor.config.forcePasteAsPlainText && window.clipboardData); // eslint-disable-line no-extra-parens
		if (!data) {
			return;
		}

		// If forcePasteAsPlainText is set, try to detect if we're with Firefox and the clipboard content is only an image
		if (CKEDITOR.env.gecko && editor.config.forcePasteAsPlainText) {
			if (data.types.length === 0) {
				// only once:
				editor.on('beforePaste', function (evt) {
					evt.removeListener();

					// Force html mode :-)
					evt.data.type = 'html';
				});
				return;
			}
		}

		// Chrome has clipboardData.items. Other browsers don't provide this info at the moment.
		// Firefox implements clipboardData.files in 22
		var dataItems = data.items;
		var items = data.files || dataItems;
		if (!items || items.length == 0) {
			return;
		}

		// Check first if there is a text/html or text/plain version, and leave the browser use that:
		// otherwise, pasting from MS Word to Chrome in Mac will always generate a black rectangle.
		if (dataItems && dataItems[0].kind) {
			// legacy code, not sure if it's still needed, but removing it would require to review different versions
			// of MacOs and Office
			for (i = 0; i < dataItems.length; i++) {
				item = dataItems[i];
				if (item.kind == 'string' && (item.type == 'text/html' || item.type == 'text/plain')) {
					return;
				}
			}
		}

		// We're safe, stupid Office-Mac combination won't disturb us.
		for (i = 0; i < items.length; i++) {
			item = items[i];
			if (item.kind && item.kind != 'file') {
				continue;
			}

			var file = item.getAsFile ? item.getAsFile() : item;
			if (!file) {
				if (window.console) {
					console.log('Failed to read file from DataTransferItem'); // eslint-disable-line no-console
				}
				continue;
			}

			e.data.preventDefault();
			e.stop();

			if (CKEDITOR.env.ie || editor.config.forcePasteAsPlainText) {
				setTimeout(function () { // eslint-disable-line no-loop-func
					processPastedFile(file, e);
				}, 100);
			} else {
				processPastedFile(file, e);
			}
		}

		// autoclose the dialog
		if (dialog && e.data.$.defaultPrevented) {
			dialog.hide();
		}
	}

	function processPastedFile(file, e) {
		var editor = e.listenerData.editor;
		var dialog = e.listenerData.dialog;

		var id = CKEDITOR.plugins.simpleuploads.getTimeStampId();
		var fileName = file.name || id + '.png';
		var evData = {
			context: e.data.$,
			name: fileName,
			file: file,
			forceLink: false,
			id: id,
			mode: {
				type: 'pastedFile',
				dialog: dialog
			}
		};

		CKEDITOR.plugins.simpleuploads.insertPastedFile(editor, evData);
	}

	function setupPasteListener(iframe) {
		var doc = iframe.getFrameDocument();
		var body = doc.getBody();
		if (!body || !body.$ || (body.$.contentEditable != 'true' && doc.$.designMode != 'on')) { // eslint-disable-line no-extra-parens
			setTimeout(function () {
				setupPasteListener(iframe);
			}, 100);
			return;
		}
		var dialog = CKEDITOR.dialog.getCurrent();

		doc.on('paste', pasteListener, null, {
			dialog: dialog,
			editor: dialog.getParentEditor()
		});
	}

	CKEDITOR.on('dialogDefinition', function (evt) {
		if (!evt.editor.plugins.simpleuploads) {
			return;
		}

		var definition = evt.data.definition;
		var defContents = definition.contents;

		// Associate filebrowser to elements with 'filebrowser' attribute.
		for (var key in defContents) {
			if ({}.hasOwnProperty.call(defContents, key)) {
				var contents = defContents[key];
				if (contents) {
					applySimpleUpload(evt.editor, evt.data.name, definition, contents.elements);
				}
			}
		}

		// Detect the Paste dialog
		if (evt.data.name == 'paste') {
			definition.onShow = CKEDITOR.tools.override(definition.onShow, function (original) {
				return function () {
					if (typeof original == 'function') {
						original.call(this);
					}

					setupPasteListener(this.getContentElement('general', 'editing_area').getInputElement());
				};
			});
		}
	}, null, null, 30);
})();

/**
 * Fired when file starts being uploaded by the 'simpleuploads' plugin
 *
 * @since 3.1
 * @name CKEDITOR.editor#simpleuploads.startUpload
 * @event
 * @param {String} [name] The file name.
 * @param {String} [url] The url that will be used for the upload. It can be modified to your needs on each upload.
 * @param {String|Object} [context] Context that caused the upload (a string if it's a pasted image, a DOM event for drag&drop and copied files, the toolbar button for those cases)
 * @param {Object} [file] The file itself (if available).
 * @param {Object} [extraFields] Since 3.4.1 the event listener can add this property to indicate extra data to send in the upload as POST data
 */

/**
 * Fired when the server sends the response of an upload.
 *
 * @since 4.3.6
 * @name CKEDITOR.editor#simpleuploads.serverResponse
 * @event
 * @param {Object} [xhr] The XHR with the request.
 * @param {Object} [data] The original data object of this upload.
 * Upon processing this event, a listener can set a 'url' property on the event.data object and that will tell to the SimpleUploads plugin
 * that your code has processed the response.
 * If url is an empty string it means that the upload has failed and that the upload placeholder must be removed silently
 * Otherwise it will be treated as the response from the server
 * This way you can use different responses from your server that doesn't follow the QuickUpload pattern, as well as hook any additional processing that
 * you might need.
 * Please, note that this is fired only for uploads using XHR, old IEs are excluded and they need the default response from the server.
 */

/**
 * Fired when file upload ends on the 'simpleuploads' plugin
 *
 * @since 3.1
 * @name CKEDITOR.editor#simpleuploads.endUpload
 * @event
 * @param {String} [name] The file name.
 * @param {Boolean} [ok] Whether the file has been correctly uploaded or not
 * @param {Object} [xhr] The XHR with the request. Since 4.3
 * @param {Object} [data] The original data object of this upload. Since 4.3
 */

/**
 * Fired when the final element has been inserted by the 'simpleuploads' plugin (after it has been uploaded)
 *
 * @since 3.3.4
 * @name CKEDITOR.editor#simpleuploads.finishedUpload
 * @event
 * @param {String} [name] The file name.
 * @param {CKEDITOR.dom.element} [element] The element node that has been inserted
 * @param {Object} [data] The original data object of this upload. Since 4.5.1.
 */

/**
 * Fired when an image has been selected, before it's uploaded. It provides a reference to an img element
 * that contains the selected file. Extends the data provided in the simpleuploads.startUpload event
 * @since 4.2
 * @name CKEDITOR.editor#simpleuploads.localImageReady
 * @event
 * @param {Image} [image] The element node that has been inserted
 */

/**
 * Class to apply to the editor container (ie: the border outside the editor) when a file is dragged on the page
 *
 *		CKEDITOR.config.simpleuploads_containerover='border:1px solid red !important;';
 *
 * @since 2.7
 * @cfg {String} [simpleuploads_containerover='box-shadow: 0 0 10px 1px #99DD99 !important;']
 * @member CKEDITOR.config
 */

/**
 * Class to apply to the editor when a file is dragged over it
 *
 *		CKEDITOR.config.simpleuploads_editorover='background-color:yellow !important;';
 *
 * @since 2.7
 * @cfg {String} [simpleuploads_editorover='box-shadow: 0 0 10px 1px #999999 inset !important;']
 * @member CKEDITOR.config
 */

/**
 * Class to apply to the dialog border/cover when a file is dragged on the page
 *
 *		CKEDITOR.config.simpleuploads_coverover='border:1px solid red !important;';
 *
 * @since 4.0
 * @cfg {String} [simpleuploads_coverover='box-shadow: 0 0 10px 4px #999999 inset !important;']
 * @member CKEDITOR.config
 */

/**
 * Class to apply to the dialog content when a file is dragged over it
 *
 *		CKEDITOR.config.simpleuploads_dialogover='border:1px solid red !important;';
 *
 * @since 4.0
 * @cfg {String} [simpleuploads_dialogover='box-shadow: 0 0 10px 4px #999999 inset !important;']
 * @member CKEDITOR.config
 */

/**
 * List of extensions that should be recognized as belonging to image files (ie: a dropped file will be inserted as img instead of link)
 *
 *		config.simpleuploads_imageExtensions='jpe?g';
 *
 * @since 3.3.3
 * @cfg {String} [simpleuploads_imageExtensions='jpe?g|gif|png']
 * @member CKEDITOR.config
 */

/**
 * Maximum file size to allow the upload. By default there are no restrictions
 *
 *		config.simpleuploads_maxFileSize=10*1024*1024; // 10 Mb
 *
 * @since 3.3.3
 * @cfg {Number} [simpleuploads_maxFileSize=null]
 * @member CKEDITOR.config
 */

/**
 * List of extensions that aren't allowed (blacklist)
 *
 *		config.simpleuploads_invalidExtensions='exe|php';
 *
 * @since 3.3.3
 * @cfg {String} [simpleuploads_invalidExtensions=null]
 * @member CKEDITOR.config
 */

/**
 * List of extensions that are accepted (whitelist). If the file doesn't have this extension it will be rejected
 *
 *		config.simpleuploads_acceptedExtensions='jpg|png|pdf|zip';
 *
 * @since 3.3.3
 * @cfg {String} [simpleuploads_acceptedExtensions=null]
 * @member CKEDITOR.config
 */

/**
 * If it's set to true, the plugin won't modify the 'Quick Upload' button in the dialogs
 * (just in case you are doing some special processing that isn't possible at the moment with the modified system)
 * (if you have such situation, please, contact me so that I can improve the plugin and allow you to use the plugin for everything)
 *
 *		config.simpleuploads_respectDialogUploads=true;
 *
 * @since 4.0
 * @cfg {Boolean} [simpleuploads_respectDialogUploads=null]
 * @member CKEDITOR.config
 */

/**
 * If it's set to true, images will be uploaded without the preview progress, using the plain text upload
 *
 *		CKEDITOR.config.simpleuploads_hideImageProgress=true;
 *
 * @since 4.1
 * @cfg {Boolean} [simpleuploads_hideImageProgress=null]
 * @member CKEDITOR.config
 */

/**
 * It's an object that can contain two members: width and height specifying the maximum dimensions (in pixels) allowed for images.
 * if the image is bigger in any of those dimensions, the upload will be rejected.
 *
 *		CKEDITOR.config.simpleuploads_maximumDimensions={width:500, height:400};
 *
 * @since 4.2
 * @cfg {Object} [simpleuploads_maximumDimensions=null]
 * @member CKEDITOR.config
 */

/**
 * Name of the input sent to the server with the file data
 *
 *		CKEDITOR.config.simpleuploads_inputname='file';
 *
 * @since 4.3.9
 * @cfg {String} [simpleuploads_inputname='upload']
 * @member CKEDITOR.config
 */
