/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
var AjaxLib = /** @class */ (function () {
    function AjaxLib() {
    }
    AjaxLib.get = function (url, data, successCallback, errorCallback) {
        AjaxLib.send("GET", url, data, successCallback, errorCallback);
    };
    AjaxLib.post = function (url, data, successCallback, errorCallback) {
        AjaxLib.send("POST", url, data, successCallback, errorCallback);
    };
    AjaxLib.put = function (url, data, successCallback, errorCallback) {
        AjaxLib.send("PUT", url, data, successCallback, errorCallback);
    };
    AjaxLib["delete"] = function (url, data, successCallback, errorCallback) {
        AjaxLib.send("DELETE", url, data, successCallback, errorCallback);
    };
    AjaxLib.send = function (requestType, url, data, successCallback, errorCallback) {
        $.ajax({
            type: requestType,
            url: url,
            data: data,
            success: successCallback,
            error: errorCallback,
            dataType: "JSON"
        });
    };
    return AjaxLib;
}());
