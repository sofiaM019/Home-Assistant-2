!function(e){function t(r){if(n[r])return n[r].exports;var s=n[r]={exports:{},id:r,loaded:!1};return e[r].call(s.exports,s,s.exports,t),s.loaded=!0,s.exports}var n={};return t.m=e,t.c=n,t.p="",t(0)}([/*!*************************************!*\
  !*** ./src/service-worker/index.js ***!
  \*************************************/
function(e,t,n){"use strict";var r="0.10",s="/",c=["/","/logbook","/history","/map","/devService","/devState","/devEvent","/devInfo","/states"],i=["/static/favicon-192x192.png"];self.addEventListener("install",function(e){e.waitUntil(caches.open(r).then(function(e){return e.addAll(i.concat(s))}))}),self.addEventListener("activate",function(e){}),self.addEventListener("message",function(e){}),self.addEventListener("fetch",function(e){var t=e.request.url.substr(e.request.url.indexOf("/",8));i.includes(t)&&e.respondWith(caches.open(r).then(function(t){return t.match(e.request)})),c.includes(t)&&e.respondWith(caches.open(r).then(function(t){return t.match(s).then(function(n){return n||fetch(e.request).then(function(e){return t.put(s,e.clone()),e})})}))})}]);
//# sourceMappingURL=service_worker.js.map