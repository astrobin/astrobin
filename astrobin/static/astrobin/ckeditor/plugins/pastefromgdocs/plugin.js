/**
 * @license Copyright (c) 2003-2025, CKSource Holding sp. z o.o. All rights reserved.
 * CKEditor 4 LTS ("Long Term Support") is available under the terms of the Extended Support Model.
 */

/**
 * @fileOverview This plugin handles pasting content from Google Docs.
 */

(function () {
    CKEDITOR.plugins.add('pastefromgdocs', {
        requires: 'pastetools',

        init: function (editor) {
            var pasteToolsPath = CKEDITOR.plugins.getPath('pastetools'), path = this.path;

            editor.pasteTools.register({
                filters: [CKEDITOR.getUrl(pasteToolsPath + 'filter/common.js')],

                canHandle: function (evt) {
                    var detectGDocsRegex = /id=(\"|\')?docs\-internal\-guid\-/;

                    return detectGDocsRegex.test(evt.data.dataValue);
                },

                handle: function (evt, next) {
                    var data = evt.data;
                    data.type = 'text';  // Force as plain text
                    next();
                }
            });
        }

    });
})();
