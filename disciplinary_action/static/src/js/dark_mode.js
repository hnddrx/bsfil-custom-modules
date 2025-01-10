odoo.define('your_module_name.dark_mode', function(require) {
    "use strict";

    var publicWidget = require('web.public.widget');

    publicWidget.registry.DarkModeToggle = publicWidget.Widget.extend({
        selector: '.oe_sidebar_action',
        
        start: function() {
            this._super.apply(this, arguments);
            // Check local storage for dark mode preference
            if (localStorage.getItem('dark_mode') === 'true') {
                this.enableDarkMode();
            }
        },

        toggleDarkMode: function() {
            var isDarkMode = localStorage.getItem('dark_mode') === 'true';
            if (isDarkMode) {
                this.disableDarkMode();
            } else {
                this.enableDarkMode();
            }
        },

        enableDarkMode: function() {
            document.body.classList.add('dark-mode');
            localStorage.setItem('dark_mode', 'true');
        },

        disableDarkMode: function() {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('dark_mode', 'false');
        },
    });

});
