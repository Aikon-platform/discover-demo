"use strict";

(function () {
    const URL_REGEX = /((([A-Za-z]{3,9}:(?:\/\/)?)(?:[\-;:&=\+\$,\w]+@)?[A-Za-z0-9\.\-]+|(?:www\.|[\-;:&=\+\$,\w]+@)[A-Za-z0-9\.\-]+)((?:\/[\+~%\/\.\w\-_]*)?\??(?:[\-\+=&;%@\.\w_]*)#?(?:[\.\!\/\\\w]*))?)/;

    class URLEntry {
        /*
        This class handles a URL element among a URL list
        */
        constructor (value, attrs, manager) {
            this.value = value;
            this.attrs = attrs;
            this.manager = manager;

            this.$element = document.createElement("li");
            this.$element.classList.add("urllist-entry");

            this.$value = document.createElement("span");
            this.$element.appendChild(this.$value);

            this.$actions = document.createElement("div");
            this.$actions.classList.add("urllist-actions");
            this.$element.appendChild(this.$actions);

            this.$edit = document.createElement("a");
            this.$edit.classList.add("urllist-edit");
            this.$actions.appendChild(this.$edit);

            this.$delete = document.createElement("a");
            this.$delete.classList.add("urllist-delete");
            this.$actions.appendChild(this.$delete);

            this.$delete.addEventListener("click", (e) => this.delete());
            this.$edit.addEventListener("click", (e) => this.startEdit());

            this.setValue(this.value);
        }

        delete () {
            this.manager.deleteURL(this);
        }

        setValue (val) {
            this.value = val;
            this.$value.innerText = val;
            if (!val.match(URL_REGEX) || (this.manager && this.manager.url_regex !== undefined && !val.match(this.manager.url_regex)))
                this.$element.classList.add("not-url");
            else
                this.$element.classList.remove("not-url");
        }

        startEdit () {
            if (this.$input === undefined) {
                this.$input = document.createElement("input");
                this.$input.type = "text";
                this.$input.addEventListener("keydown", (e) => this.handleKeyPressed(e));
                this.$input.addEventListener("blur", () => this.endEdit());
            }
            this.$input.value = this.value;
            this.$element.appendChild(this.$input);
            this.$input.focus();
            this.$element.classList.add("editing");
        }

        handleKeyPressed (event) {
            switch (event.keyCode) {
                case 13:
                    event.preventDefault();
                    this.endEdit();
            }
        }

        endEdit () {
            if (!this.$input.parentNode)
                return

            this.setValue(this.$input.value);
            this.manager.syncInput();

            this.$input.remove();
            this.$element.classList.remove("editing");
        }

        destroy () {
            this.$delete.remove();
            this.$element.remove();
        }
    };

    class URLListField {
        /*
        This class is a smart URL list input field controller
        It mostly handles copy-pasting a list of urls
        Duplicates are removed
        TODO : handle history
        */
        constructor (input, url_regex) {
            this.$input = input;
            this.url_regex = url_regex;

            this.$input.style.display = "none";

            // An element to wrap the modified input
            this.$wrapper = document.createElement("div");
            this.$wrapper.classList.add("urllist-wrapper");
            this.$input.parentElement.insertBefore(this.$wrapper, this.$input);

            // The list of url container
            this.$list = document.createElement("ul");
            this.$list.classList.add("urllist-list");
            this.$wrapper.appendChild(this.$list);

            // The free input to add new URLs
            this.$append = document.createElement("textarea");
            this.$append.placeholder = "Type or paste URLs to append to the list above";
            this.$append.classList.add("urllist-input", "input");
            this.$wrapper.appendChild(this.$append);
            this.$append.addEventListener("input", (e) => this.handleInput(e));

            this._value = null;
            this._prev_append = "";
            this.urls = [];
            this.url_set = new Set();

            this.value = this.$input.value;
        }

        set value (value) {
            if (value != this._value) {
                this.updateFromScratch(value);
                this._value = value;
                this.syncInput();
            }
        }

        updateFromScratch (raw) {
            // (Re)-create the list of URLs

            for (let i=0; i<this.urls.length; i++) {
                this.urls[i].destroy();
            }

            let data = JSON.parse(raw);

            if (data === null) data = [];

            this.urls = [];
            this.url_set.clear();

            this.appendURLs(data);
        }

        appendURLs (urllist, raw) {
            for(let i=0; i<urllist.length; i++) {
                let url = urllist[i];
                let attrs = [];
                if (!raw) {
                    attrs = url.slice(1);
                    url = url[0];
                }
                url = url.trim();

                if (url == "" || this.url_set.has(url)) continue;
                let newURL = new URLEntry(url, attrs, this);

                this.$list.appendChild(newURL.$element);
                this.urls.push(newURL);
                this.url_set.add(url);
            }
            this.syncInput();
        }

        appendRawValues (raw) {
            let data = raw.split(/[\s;,]+/gis);
            this.appendURLs(data, true);
        }

        syncInput () {
            // Update the form input value
            let val = [];
            for (let i=0; i<this.urls.length; i++) {
                val.push(
                    [this.urls[i].value, ...this.urls[i].attrs]
                );
            }
            this._value = JSON.stringify(val);
            this.$input.value = this._value;
        }

        handleInput (e) {
            let val = this.$append.value;
            switch (e.inputType) {
                case "insertFromPaste":
                case "insertFromDrop":
                case "interFromYank":
                    this.appendRawValues(e.data || val);
                    this.$append.value = this._prev_append;
                    break;
            }
            if (e.inputType.slice(0, 6) == "insert") {
                if (e.inputType == "insertParagraph" || e.inputType == "insertLineBreak"
                    || e.data == "," || e.data == "," || e.data == " ") {
                    this.appendRawValues(val);
                    this.$append.value = "";
                }
            }
            this._prev_append = this.$append.value;
        }

        deleteURL (urlentry) {
            let i = this.urls.indexOf(urlentry);
            if (i >= 0) {
                this.url_set.delete(urlentry.value);
                this.urls.splice(i, 1);
                this.syncInput();
            }
            urlentry.destroy();
        }
    };

    URLListField.autoInit = () => {
        let items = document.querySelectorAll(".urllistfield");
        for (let i=0; i<items.length; i++) {
            new URLListField(items[i], undefined);
        }
    };

    window.URLListField = (...args) => (new URLListField(...args));
    document.addEventListener("DOMContentLoaded", URLListField.autoInit);
})();
