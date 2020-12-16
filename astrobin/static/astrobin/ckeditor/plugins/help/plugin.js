CKEDITOR.plugins.add('help', {
    icons: 'help',
    init: function (editor) {
        editor.addCommand('help', new CKEDITOR.command(editor, {
            exec: function () {
                window.open('https://welcome.astrobin.com/features/rich-content-editor/', '_blank');
            }
        }));

        editor.ui.addButton('HelpButton', {
            title: 'Help',
            icon: CKEDITOR.getUrl(this.path) + 'icons/help.png',
            command: 'help'
        });
    }
});
