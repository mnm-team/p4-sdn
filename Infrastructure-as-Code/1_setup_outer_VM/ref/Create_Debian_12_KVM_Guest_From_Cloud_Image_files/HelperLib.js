/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
var HelperLib = /** @class */ (function () {
    function HelperLib() {
    }
    HelperLib.isInternetExplorer = function () {
        var isIe = true;
        var ua = window.navigator.userAgent;
        var msie = ua.indexOf("MSIE ");
        if (msie > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./)) {
            isIe = true;
        }
        else {
            isIe = false;
        }
        return isIe;
    };
    /**
     * Detect if the browser is internet explorer, and show a browser not supported message
     * if it is.
     */
    HelperLib.bailOutIfInternetExplorer = function () {
        if (HelperLib.isInternetExplorer()) {
            document.body.innerHTML = "";
            var centerTag = document.createElement("center");
            var noticeDiv = document.createElement("div");
            var headerTitle = document.createElement("h1");
            headerTitle.innerHTML = "Browser not supported.";
            var paragraph = document.createElement("p");
            paragraph.style.cssText = "max-width: 33rem;";
            paragraph.innerHTML =
                "We have detected that you are using Internet Explorer which is not supported. " +
                    "Please switch to a modern browser such as <a href='https://www.mozilla.org/en-GB/firefox/new/'>Firefox</a> " +
                    "or <a href='https://www.google.com/chrome/'>Chrome</a>.";
            noticeDiv.appendChild(headerTitle);
            noticeDiv.appendChild(paragraph);
            centerTag.appendChild(noticeDiv);
            document.body.appendChild(centerTag);
        }
    };
    // https://stackoverflow.com/questions/1064089/inserting-a-text-where-cursor-is-using-javascript-jquery
    HelperLib.insertAtCaret = function (txtarea, text) {
        var scrollPos = txtarea.scrollTop;
        var strPos = 0;
        strPos = txtarea.selectionStart;
        var front = (txtarea.value).substring(0, strPos);
        var back = (txtarea.value).substring(strPos, txtarea.value.length);
        txtarea.value = front + text + back;
        strPos = strPos + text.length;
        txtarea.selectionStart = strPos;
        txtarea.selectionEnd = strPos;
        txtarea.focus();
        txtarea.scrollTop = scrollPos;
    };
    // https://stackoverflow.com/questions/5379120/get-the-highlighted-selected-text
    HelperLib.getSelectionText = function () {
        var text = "";
        var activeEl = document.activeElement;
        var activeElTagName = activeEl ? activeEl.tagName.toLowerCase() : null;
        if ((activeElTagName == "textarea")
            || (activeElTagName == "input" && /^(?:text|search|password|tel|url)$/i.test(activeEl.type))
                && (typeof activeEl.selectionStart == "number")) {
            text = activeEl.value.slice(activeEl.selectionStart, activeEl.selectionEnd);
        }
        else if (window.getSelection) {
            text = window.getSelection().toString();
        }
        return text;
    };
    /**
     * Replace text in an html text area element.
     * https://stackoverflow.com/questions/34968174/set-text-cursor-position-in-a-textarea
     */
    HelperLib.replaceText = function (el, replacementText, offset) {
        var end = el.selectionEnd;
        var val = el.value;
        el.value = val.slice(0, el.selectionStart) + replacementText + val.slice(el.selectionEnd);
        el.focus();
        el.selectionEnd = end + offset;
    };
    return HelperLib;
}());
