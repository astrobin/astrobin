CKEDITOR.plugins.setLang( 'simpleuploads', 'en',
	{
		// Tooltip for the "add file" toolbar button
		addFile: 'Add a file',
		// Tooltip for the "add image" toolbar button
		addImage: 'Add an image',

		// The server returned a URL after the upload that it's wrong
		badUrl: 'Failed to load the image with the provided URL',

		// Generic error for http status codes. Specific ones can be defined as 'httpStatus400', etc...
		errorPostFile: 'Error posting the file to %0\r\nResponse status:',

		// File size is over config.simpleuploads_maxFileSize OR the server returns HTTP status 413
		fileTooBig: 'The file is too big, please use a smaller one.',

		// the 4 FailedTo messages can happen in Safari until they fix pasting files from Finder
		FailedToComputePreviewImageSize: 'Failed to compute the preview size. Try to drop it instead.',
		FailedToLoadPreviewImage: 'Failed to display the preview image. Try to drop it instead.',
		FailedToReadTheFile: 'Failed to read the file. Try to drop it instead.',
		FailedToReadTheImage: 'Failed to read the image. Try to drop it instead.',

		// The height of the image is over the allowed maximum
		imageTooTall: 'The image is too tall',

		// The width of the image is over the allowed maximum
		imageTooWide: 'The image is too wide',

		// The extension matches one of the blacklisted ones in config.simpleuploads_invalidExtensions
		invalidExtension: 'Invalid file type, please use only valid files.',

		// The extension isn't included in config.simpleuploads_acceptedExtensions
		nonAcceptedExtension: 'The file type is not valid, please use only valid files:\r\n%0',

		// The file isn't an accepted type for images
		nonImageExtension: 'You must select an image',

		// Shown after the data has been sent to the server and we're waiting for the response
		processing: 'Processing...',

		// images with webkit-fake-url can't be read
		uselessSafari: 'Sorry, this version of Safari doesn\'t allow to paste images',

		// Error in the XHR upload. I'm not sure under which conditions this could happen, but it's a safety check
		xhrError: 'Error posting the file to %0'
	}
);
