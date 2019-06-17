(function ($) {
    $.fn.nested_comments = function () {
        var $el = this;
        var $form = $el.find('.top-level-form form');
        var $loader = $form.find('.loader');
        var $button = $form.find('input[type=submit]');
        var $textarea = $form.find('textarea');

        var resetForm = function ($form) {
            $loader.css('visibility', 'hidden');
            $button.removeAttr('disabled').removeClass('disabled');
        };

        var ajaxFormOptions = {
            dataType: 'json',
            timeout: 10000,
            clearForm: true,
            beforeSubmit: function (formData, $form, options) {
                if ($textarea.val() == '') return false;

                $button.attr('disabled', 'disabled').addClass('disabled');
                $loader.css('visibility', 'visible');
            },
            success: function (responseJson, statusText, xhr, $form) {
                resetForm($form);
            }
        };

        $form.ajaxForm(ajaxFormOptions);
    }
})(window.jQuery);
