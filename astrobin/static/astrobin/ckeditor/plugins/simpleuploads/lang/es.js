CKEDITOR.plugins.setLang( 'simpleuploads', 'es',
	{
		// Tooltip for the "add file" toolbar button
		addFile: 'Añadir un fichero',
		// Tooltip for the "add image" toolbar button
		addImage: 'Añadir una imagen',

		// The server returned a URL after the upload that it's wrong
		badUrl: 'No se ha podido mostrar la imagen con la URL indicada',

		// Generic error for http status codes. Specific ones can be defined as 'httpStatus400', etc...
		errorPostFile: 'Error enviando el fichero a %0\r\nCódigo de estado:',

		// File size is over config.simpleuploads_maxFileSize OR the server returns HTTP status 413
		fileTooBig: 'El fichero es demasiado grande, por favor, escoja uno menor.',

		// the 4 FailedTo messages can happen in Safari until they fix pasting files from Finder
		FailedToComputePreviewImageSize: 'No se ha podido calcular el tamaño de la previsualización. Pruebe a arrastrar el fichero.',
		FailedToLoadPreviewImage: 'No se ha podido cargar la previsualización. Pruebe a arrastrar el fichero.',
		FailedToReadTheFile: 'No se ha podido leer el fichero. Pruebe a arrastrar el fichero.',
		FailedToReadTheImage: 'No se ha podido leer la imagen. Pruebe a arrastrar el fichero.',

		// The height of the image is over the allowed maximum
		imageTooTall: 'La imagen es demasiado alta',

		// The width of the image is over the allowed maximum
		imageTooWide: 'La imagen es demasiado ancha',

		// The extension matches one of the blacklisted ones in config.simpleuploads_invalidExtensions
		invalidExtension: 'Este tipo de fichero no está permitido.',

		// The extension isn't included in config.simpleuploads_acceptedExtensions
		nonAcceptedExtension: 'El tipo de fichero no es válido, por favor elija uno correcto:\r\n%0',

		// The file isn't an accepted type for images
		nonImageExtension: 'Debe seleccionar una imagen',

		// Shown after the data has been sent to the server and we're waiting for the response
		processing: 'Procesando...',

		// images with webkit-fake-url can't be read
		uselessSafari: 'Lo sentimos, esta versión de Safari no permite pegar imágenes',

		// Error in the XHR upload. I'm not sure under which conditions this could happen, but it's a safety check
		xhrError: 'Error enviando el fichero a %0'
	}
);
